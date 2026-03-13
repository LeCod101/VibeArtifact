/**
 * 根布局组件
 * 引入 Space Grotesk（标题字体）和 Inter（正文字体）
 * 通过 CSS 变量 --font-heading 和 --font-body 提供给全局样式使用
 */
import type { Metadata } from "next";
import { Space_Grotesk, Inter, Geist_Mono, JetBrains_Mono } from "next/font/google";
import { I18nProvider } from "@/i18n/context";
import { QueryProvider } from "@/lib/query-client";
import { Toaster } from "@/components/ui/sonner";
import "./globals.css";

// 标题字体 - Space Grotesk（Anthropic 风格的免费替代）
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-heading",
  display: "swap",
});

// 正文字体 - Inter
const inter = Inter({
  subsets: ["latin"],
  variable: "--font-body",
  display: "swap",
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// 等宽终端风字体 - JetBrains Mono（用于统计数字展示）
const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono-jb",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VibeArtifact — AI Product Engineering OS",
  description:
    "Stop writing code. Start generating systems. VibeArtifact automatically generates and deploys production-grade full-stack architectures from a single sentence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh" suppressHydrationWarning>
      <body
        className={`${spaceGrotesk.variable} ${inter.variable} ${geistMono.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <I18nProvider>
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
