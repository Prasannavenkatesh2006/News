"""
X (Twitter) scraper.
Uses Twitter API v2 via tweepy if bearer token is set.
Falls back to ntscraper (no auth) for basic trending data.
"""
import os
import sys
import time
import logging
import schedule

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.kafka_publisher import publish_to_kafka
from common.rate_limiter import rate_limit, BackoffRetry

logging.basicConfig(level=logging.INFO, format='%(asctime)s [X/Twitter] %(message)s')
logger = logging.getLogger(__name__)

TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN", "")
seen_ids: set = set()


@BackoffRetry(max_retries=2, base_delay=10.0)
def scrape_x_api():
    """Use official Twitter API v2 (requires Bearer Token)."""
    if not TWITTER_BEARER or TWITTER_BEARER in ("", "your_twitter_bearer_token"):
        return False

    try:
        import tweepy
        client = tweepy.Client(bearer_token=TWITTER_BEARER, wait_on_rate_limit=True)

        # Search recent high-engagement tweets on trending topics
        queries = [
            "technology AI lang:en -is:retweet",
            "breaking news lang:en -is:retweet",
            "India trending lang:en -is:retweet",
        ]

        posted = 0
        for query in queries:
            try:
                tweets = client.search_recent_tweets(
                    query=f"{query} min_faves:500",
                    max_results=10,
                    tweet_fields=["public_metrics", "created_at", "author_id", "context_annotations"],
                    expansions=["author_id"],
                    user_fields=["username", "name"],
                )

                if not tweets.data:
                    continue

                # Build user map
                users = {}
                if tweets.includes and "users" in tweets.includes:
                    for u in tweets.includes["users"]:
                        users[str(u.id)] = u

                for tweet in tweets.data:
                    tid = str(tweet.id)
                    if tid in seen_ids:
                        continue
                    seen_ids.add(tid)

                    metrics = tweet.public_metrics or {}
                    likes = metrics.get("like_count", 0)
                    retweets = metrics.get("retweet_count", 0)
                    replies = metrics.get("reply_count", 0)

                    if likes < 500:
                        continue

                    author = users.get(str(tweet.author_id))
                    author_str = f"@{author.username}" if author else "Unknown"

                    content = (
                        f"{tweet.text}\n\n"
                        f"— {author_str}\n"
                        f"❤️ {likes:,} likes · 🔁 {retweets:,} retweets · 💬 {replies:,} replies"
                    )

                    publish_to_kafka({
                        "type": "x_trending",
                        "title": f"🐦 Viral on X: {tweet.text[:80]}...",
                        "content": content,
                        "source": f"X ({author_str})",
                        "url": f"https://twitter.com/i/web/status/{tid}",
                        "platform": "x",
                        "upvotes": likes,
                        "topic_hint": "technology",
                        "metadata": {"tweet_id": tid, "likes": likes, "retweets": retweets},
                    })
                    posted += 1

                time.sleep(2)
            except Exception as e:
                logger.warning(f"Query failed ({query[:30]}...): {e}")

        logger.info(f"✅ X API: {posted} tweets published")
        return True

    except ImportError:
        logger.warning("tweepy not installed")
        return False
    except Exception as e:
        logger.error(f"X API error: {e}")
        return False


def scrape_x_free():
    """
    Free fallback: Scrape X/Twitter trending topics via ntscraper
    or use public RSS-like endpoint.
    """
    try:
        # Try ntscraper (no auth required)
        from ntscraper import Nitter

        scraper = Nitter(log_level=1, skip_instance_check=False)
        topics = ["AI technology", "breaking news", "India"]

        posted = 0
        for topic in topics:
            try:
                tweets = scraper.get_tweets(topic, mode="hashtag", number=5)
                for tweet in tweets.get("tweets", []):
                    tid = tweet.get("link", "").split("/")[-1]
                    if tid in seen_ids:
                        continue
                    seen_ids.add(tid)

                    stats = tweet.get("stats", {})
                    likes = stats.get("likes", 0)
                    text = tweet.get("text", "")

                    if likes < 100:
                        continue

                    publish_to_kafka({
                        "type": "x_trending",
                        "title": f"🐦 X Trending: {text[:80]}",
                        "content": f"{text}\n\n❤️ {likes} likes",
                        "source": "X (Twitter)",
                        "url": tweet.get("link", ""),
                        "platform": "x",
                        "upvotes": likes,
                        "topic_hint": "technology",
                    })
                    posted += 1
            except Exception:
                pass

        if posted:
            logger.info(f"✅ X (ntscraper): {posted} tweets published")
        return posted > 0
    except ImportError:
        pass

    # Last resort: Rss-bridge or public JSON
    logger.debug("X scraper: no method available (needs TWITTER_BEARER_TOKEN or ntscraper)")
    return False


def scrape_x():
    logger.info("🐦 Scraping X/Twitter...")
    if not scrape_x_api():
        scrape_x_free()


def main():
    logger.info("🚀 X scraper starting...")
    scrape_x()
    schedule.every(2).minutes.do(scrape_x)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
