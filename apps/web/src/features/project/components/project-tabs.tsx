/**
 * 项目内导航标签栏 - 所有项目子页面共享
 *
 * 根据当前路径自动高亮激活标签，支持移动端横向滚动。
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Lightbulb,
  Rocket,
  History,
  Package,
} from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

/** 标签定义 */
function getTabs(projectId: string) {
  return [
    {
      href: `/projects/${projectId}/overview`,
      label: t.project.overview,
      icon: LayoutDashboard,
    },
    {
      href: `/projects/${projectId}`,
      label: t.project.conversations,
      icon: MessageSquare,
      // 对话页是精确匹配，不是前缀匹配
      exact: true,
    },
    {
      href: `/projects/${projectId}/ideation`,
      label: t.generation.ideationTitle,
      icon: Lightbulb,
    },
    {
      href: `/projects/${projectId}/delegation`,
      label: t.delegation.tab,
      icon: Rocket,
    },
    {
      href: `/projects/${projectId}/runs`,
      label: t.project.runs,
      icon: History,
    },
    {
      href: `/projects/${projectId}/artifacts`,
      label: t.project.artifacts,
      icon: Package,
    },
  ];
}

interface ProjectTabsProps {
  projectId: string;
}

/** 项目导航标签栏组件 */
export function ProjectTabs({ projectId }: ProjectTabsProps) {
  const pathname = usePathname();
  const { locale } = useLocale();
  const tabs = getTabs(projectId);

  /** 判断当前标签是否激活 */
  function isActive(tab: (typeof tabs)[number]) {
    if (tab.exact) {
      return pathname === tab.href;
    }
    return pathname === tab.href || pathname.startsWith(tab.href + "/");
  }

  return (
    <nav className="flex items-center gap-1 overflow-x-auto scrollbar-none">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const active = isActive(tab);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              active
                ? "bg-secondary text-foreground"
                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
            }`}
          >
            <Icon size={16} />
            {L(tab.label, locale)}
          </Link>
        );
      })}
    </nav>
  );
}
