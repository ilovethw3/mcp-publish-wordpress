import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { ToastProvider } from '@/contexts/ToastContext';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'MCP WordPress Publisher v2.1 - 管理控制台',
  description: '多代理多站点WordPress内容发布管理系统',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <ToastProvider>
          <div className="min-h-screen bg-gray-50">
            {children}
          </div>
        </ToastProvider>
      </body>
    </html>
  );
}