"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

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
    <nav className="bg-slate-900 border-b border-slate-800 text-white sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center w-full justify-between">
            <div className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold tracking-wider text-red-500 flex items-center gap-2">
                <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse"></span>
                FAUD-DETECT<span className="text-slate-400 font-light text-sm">v1.0</span>
              </span>
            </div>
            
            <div className="hidden sm:ml-6 sm:flex sm:space-x-4">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`inline-flex items-center px-4 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-red-600 text-white shadow-lg shadow-red-900/30'
                        : 'text-slate-300 hover:bg-slate-800 hover:text-white'
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
      <div className="sm:hidden flex justify-around border-t border-slate-800 bg-slate-950 py-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`text-xs px-2 py-1.5 rounded-md font-medium transition-all ${
                isActive ? 'text-red-500 font-bold bg-slate-900' : 'text-slate-400 hover:text-white'
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
