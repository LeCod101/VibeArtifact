/**
 * 登录页面
 *
 * 邮箱 + 密码表单，登录成功后存 token、获取用户信息、跳转仪表盘。
 */
"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useLoginMutation, useMeQuery } from "@/features/auth/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

export default function LoginPage() {
  const { locale } = useLocale();
  const router = useRouter();
  const loginMutation = useLoginMutation();
  const { refetch: fetchMe } = useMeQuery();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      await loginMutation.mutateAsync({ email, password });
      // 登录成功，获取用户信息
      await fetchMe();
      toast.success(L(t.auth.loginSuccess, locale));
      router.push("/dashboard");
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  return (
    <Card className="w-full max-w-md">
      <CardHeader className="text-center">
        {/* Logo */}
        <svg viewBox="0 0 300 250" className="h-16 w-auto mx-auto text-foreground mb-2">
          <g fill="currentColor">
            <polygon points="85,40 119,108 109,128 65,40" />
            <polygon points="165,40 185,40 235,140 215,140 175,60 125,160 115,140 165,40" />
            <polygon points="150.5,105 199.5,105 207,120 143,120" />
          </g>
          <text
            x="150" y="215"
            fontFamily="'Inter', sans-serif"
            fontSize="32" fontWeight="600"
            letterSpacing="-0.02em"
            textAnchor="middle"
            fill="currentColor"
          >
            VibeArtifact
          </text>
        </svg>
        <CardTitle className="text-2xl">{L(t.auth.loginTitle, locale)}</CardTitle>
        <CardDescription>
          {L(t.auth.noAccount, locale)}{" "}
          <Link href="/register" className="text-primary underline underline-offset-4">
            {L(t.auth.goRegister, locale)}
          </Link>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">{L(t.auth.email, locale)}</Label>
            <Input
              id="email"
              type="email"
              placeholder={L(t.auth.emailPlaceholder, locale)}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">{L(t.auth.password, locale)}</Label>
            <Input
              id="password"
              type="password"
              placeholder={L(t.auth.passwordPlaceholder, locale)}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
          <Button
            type="submit"
            className="w-full"
            disabled={loginMutation.isPending}
          >
            {loginMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {L(t.auth.loginBtn, locale)}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
