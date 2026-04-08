/**
 * 工作区空状态欢迎与建议提问
 *
 * 在无消息且非流式时展示，点击建议可快速发起首轮对话。
 */
"use client";

import { BookOpen, Code2, FileText, Rocket, Sparkles } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const SUGGESTIONS: {
  text: string;
  icon: typeof Code2;
}[] = [
  { text: "帮我设计一个 Java 二叉树实现", icon: Code2 },
  { text: "解释快速排序算法的时间复杂度", icon: BookOpen },
  { text: "生成一个 Spring Boot REST API 模板", icon: Rocket },
  { text: "帮我写一份数据库设计文档", icon: FileText },
];

export interface WorkspaceWelcomeProps {
  projectName?: string;
  onSuggestionClick: (text: string) => void;
}

export function WorkspaceWelcome({
  projectName,
  onSuggestionClick,
}: WorkspaceWelcomeProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[min(420px,50vh)] w-full max-w-2xl mx-auto py-6 px-2">
      <div className="mb-8 text-center space-y-2">
        <div className="inline-flex items-center justify-center rounded-full bg-primary/10 p-3 text-primary mb-1">
          <Sparkles className="h-6 w-6" aria-hidden />
        </div>
        <h2 className="text-lg font-semibold tracking-tight">
          {projectName ? `在「${projectName}」中开始` : "开始对话"}
        </h2>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          描述你的需求，Agent 会思考、调用工具并生成代码与文档。也可以从下方示例一键开始。
        </p>
      </div>

      <div className="grid w-full gap-3 sm:grid-cols-2">
        {SUGGESTIONS.map(({ text, icon: Icon }) => (
          <button
            key={text}
            type="button"
            onClick={() => onSuggestionClick(text)}
            className={cn(
              "text-left rounded-xl transition-all",
              "hover:ring-2 hover:ring-primary/20 hover:shadow-md",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            )}
          >
            <Card
              size="sm"
              className="h-full cursor-pointer py-3 px-3 hover:bg-accent/40"
            >
              <div className="flex gap-3 items-start">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <span className="text-sm leading-snug pt-1">{text}</span>
              </div>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}
