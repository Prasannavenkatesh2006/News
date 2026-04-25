import './globals.css';
import type { Metadata } from 'next';
import Providers from './providers';
import FloatingChat from '@/components/FloatingChat';


export const metadata: Metadata = {
    title: 'PULSE — The Heartbeat of Global Information',
    description: 'PULSE is a next-generation AI-driven social intelligence platform that transforms global news into real-time, interactive, community-driven insights. Combines multi-source data ingestion, machine learning, and social engagement to detect and surface important events as they happen.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
    return (
        <html lang="en" className="light" suppressHydrationWarning>
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <meta name="theme-color" content="#0b0f19" />
            </head>
            <body suppressHydrationWarning>
              <Providers>
                {children}
                <FloatingChat />
              </Providers>
            </body>
        </html>
    );
}

