'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, LangSwitch } from '@/lib/locale-context';

export default function NavBar() {
  const pathname = usePathname();
  const { locale } = useLocale();
  const zh = locale === 'zh';
  const [open, setOpen] = useState(false);

  const links = [
    { href: '/', label: zh ? '首页' : 'Home' },
    { href: '/simulate', label: zh ? '社会模拟' : 'Simulation' },
    { href: '/survey', label: zh ? '市场调研' : 'Survey' },
    { href: '/data', label: zh ? '数据质量' : 'Data Quality' },
    { href: '/cases', label: zh ? '案例验证' : 'Cases' },
    { href: '/research', label: zh ? '研究基础' : 'Research' },
    { href: '/about', label: zh ? '系统介绍' : 'About' },
  ];

  return (
    <nav className="border-b border-[#1e293b] bg-[#0a0e1a]/90 backdrop-blur sticky top-0 z-50">
      <div className="flex items-center justify-between px-4 sm:px-6 py-3">
        <div className="flex items-center gap-4 sm:gap-6">
          <Link href="/" className="text-sm sm:text-base font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent whitespace-nowrap">
            {zh ? '新加坡数字孪生' : 'SG Digital Twin'}
          </Link>
          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 text-xs rounded-lg font-medium transition-all ${
                  pathname === link.href
                    ? 'text-blue-400 bg-blue-500/10'
                    : 'text-[#94a3b8] hover:text-[#e2e8f0] hover:bg-[#111827]'
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <LangSwitch />
          <span className="hidden sm:inline text-xs text-[#475569] font-mono">172,173 {zh ? 'AI 市民' : 'AI Citizens'}</span>
          {/* Hamburger */}
          <button onClick={() => setOpen(!open)} className="md:hidden p-1.5 rounded-lg text-[#94a3b8] hover:bg-[#111827]">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
              {open
                ? <path d="M5 5l10 10M15 5L5 15" />
                : <path d="M3 6h14M3 10h14M3 14h14" />}
            </svg>
          </button>
        </div>
      </div>
      {/* Mobile menu */}
      {open && (
        <div className="md:hidden border-t border-[#1e293b] px-4 py-2 space-y-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={`block px-3 py-2.5 text-sm rounded-lg font-medium transition-all ${
                pathname === link.href
                  ? 'text-blue-400 bg-blue-500/10'
                  : 'text-[#94a3b8] hover:text-[#e2e8f0] hover:bg-[#111827]'
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="px-3 py-2 text-xs text-[#475569] font-mono">172,173 {zh ? 'AI 市民智能体' : 'AI Citizens'}</div>
        </div>
      )}
    </nav>
  );
}
