import { ArrowBigUp } from 'lucide-react';
import { motion } from 'framer-motion';

interface VoteButtonsProps {
  postId: string | number;
  initialUpvotes: number;
  initialDownvotes: number;
  onVote?: (id: string | number, dir: 1 | -1) => void;
}

export function VoteButtons({ postId, initialUpvotes, initialDownvotes, onVote }: VoteButtonsProps) {
  const netVotes = initialUpvotes - initialDownvotes;

  return (
    <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
      <motion.button 
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="p-1.5 rounded-lg hover:bg-emerald-50 hover:text-emerald-600 text-slate-400 transition-colors"
        onClick={() => onVote && onVote(postId, 1)}
      >
        <ArrowBigUp className="w-6 h-6" />
      </motion.button>
      
      <span className={`text-sm font-bold ${
        netVotes > 0 ? 'text-emerald-600' : 
        netVotes < 0 ? 'text-rose-600' : 
        'text-slate-500'
      }`}>
        {netVotes > 0 ? `+${netVotes}` : netVotes}
      </span>
      
      <motion.button 
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        className="p-1.5 rounded-lg hover:bg-rose-50 hover:text-rose-600 text-slate-400 transition-colors"
        onClick={() => onVote && onVote(postId, -1)}
      >
        <ArrowBigUp className="w-6 h-6 rotate-180" />
      </motion.button>
    </div>
  );
}
