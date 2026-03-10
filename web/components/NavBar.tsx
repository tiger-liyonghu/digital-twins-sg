'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useLocale, LangSwitch } from '@/lib/locale-context';

export default function NavBar() {
  const pathname = usePathname();
  const { locale } = useLocale();
  const zh = locale === 'zh';

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
    <nav className="flex items-center justify-between px-6 py-3 border-b border-[#1e293b] bg-[#0a0e1a]/90 backdrop-blur sticky top-0 z-50">
      <div className="flex items-center gap-6">
        <Link href="/" className="text-base font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          {zh ? '新加坡数字孪生' : 'Singapore Digital Twin'}
        </Link>
        <div className="flex items-center gap-1">
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
      <div className="flex items-center gap-4">
        <LangSwitch />
        <span className="text-xs text-[#475569] font-mono">172,173 {zh ? 'AI 市民孪生智能体' : 'AI Citizens'}</span>
      </div>
    </nav>
  );
}
