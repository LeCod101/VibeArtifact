/**
 * 设置页 - 用户个人设置
 *
 * 包含个人信息展示、语言切换、密码修改（占位）。
 */
"use client";

import { User, Globe, Shield } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useAuthStore } from "@/stores/auth-store";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function SettingsPage() {
  const { locale, toggleLocale } = useLocale();
  const { user } = useAuthStore();

  return (
    <div className="max-w-3xl mx-auto">
      {/* 页面标题 */}
      <div className="mb-8 animate-reveal">
        <h1 className="font-heading text-2xl font-bold tracking-tight">
          {L(t.settings.title, locale)}
        </h1>
      </div>

      <div className="space-y-6">
        {/* 个人信息区 */}
        <Card
          className="animate-reveal"
          style={{ animationDelay: "0.05s" }}
        >
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <User size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">
                {L(t.settings.profile, locale)}
              </h2>
            </div>

            <div className="space-y-4">
              {/* 用户名 */}
              <div className="space-y-2">
                <Label>{L(t.settings.username, locale)}</Label>
                <Input
                  value={user?.display_name || ""}
                  disabled
                  className="bg-muted"
                />
              </div>

              {/* 邮箱 */}
              <div className="space-y-2">
                <Label>{L(t.settings.email, locale)}</Label>
                <Input
                  value={user?.email || ""}
                  disabled
                  className="bg-muted"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 外观设置区 */}
        <Card
          className="animate-reveal"
          style={{ animationDelay: "0.1s" }}
        >
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Globe size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">
                {L(t.settings.appearance, locale)}
              </h2>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">
                  {L(t.settings.language, locale)}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {locale === "zh" ? "当前：简体中文" : "Current: English"}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleLocale}
              >
                {locale === "zh" ? "English" : "中文"}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* 安全区 */}
        <Card
          className="animate-reveal"
          style={{ animationDelay: "0.15s" }}
        >
          <CardContent className="p-6">
            <div className="flex items-center gap-3 mb-6">
              <Shield size={20} className="text-foreground/70" />
              <h2 className="text-base font-bold">
                {L(t.settings.security, locale)}
              </h2>
              <Badge variant="secondary" className="text-[10px]">
                {L(t.settings.comingSoon, locale)}
              </Badge>
            </div>

            <div className="space-y-4 opacity-50 pointer-events-none">
              {/* 当前密码 */}
              <div className="space-y-2">
                <Label>{L(t.settings.currentPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>

              {/* 新密码 */}
              <div className="space-y-2">
                <Label>{L(t.settings.newPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>

              {/* 确认密码 */}
              <div className="space-y-2">
                <Label>{L(t.settings.confirmPassword, locale)}</Label>
                <Input type="password" disabled />
              </div>

              <Button disabled>
                {L(t.settings.save, locale)}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
