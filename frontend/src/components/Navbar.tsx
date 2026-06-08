"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import Image from 'next/image';

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { name: 'Overview', href: '/' },
    { name: 'Risk Scoring', href: '/risk' },
    { name: 'Graph Analytics', href: '/graph' },
    { name: 'Model Inference', href: '/inference' },
    { name: 'AI Chatbot', href: '/chatbot' },
  ];

  return (
    <nav className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-slate-800 dark:text-white sticky top-0 z-50 shadow-sm transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center w-full justify-between">
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="flex items-center">
                <Image 
                  src="/logo.png" 
                  alt="V-TEKI Logo" 
                  width={180} 
                  height={60} 
                  className="h-12 md:h-14 w-auto object-contain dark:brightness-0 dark:invert transition-all"
                  priority
                />
              </Link>
            </div>
            
            <div className="hidden md:flex items-center space-x-6">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`inline-flex items-center px-1 py-2 text-sm font-semibold transition-all duration-200 ${
                      isActive
                        ? 'text-v-blue border-b-2 border-v-blue'
                        : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </div>
            
          </div>
        </div>
      </div>
      
      {/* Mobile nav indicator bar */}
      <div className="md:hidden flex justify-around border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 py-2 transition-colors duration-300">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`text-xs px-2 py-1.5 rounded-md font-medium transition-all ${
                isActive ? 'text-v-blue font-bold bg-blue-50 dark:bg-slate-800' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
