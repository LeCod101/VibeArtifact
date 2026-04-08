/**
 * 新建项目表单 - 项目类型、名称与描述，成功后进入工作区
 */
"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useCreateProjectMutation } from "@/features/project/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client/errors";

const PROJECT_TYPES = [
  { value: "homework", label: "作业", icon: "📝" },
  { value: "thesis", label: "毕设", icon: "🎓" },
  { value: "personal", label: "个人项目", icon: "🚀" },
] as const;

export function CreateProjectForm() {
  const router = useRouter();
  const createMutation = useCreateProjectMutation();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [projectType, setProjectType] = useState<string>("homework");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;

    try {
      const project = await createMutation.mutateAsync({
        name: trimmed,
        description: description.trim() || undefined,
        project_type: projectType,
      });
      toast.success("项目创建成功");
      router.push(`/project/${project.id}`);
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : "创建失败，请重试";
      toast.error(msg);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-lg">
      <div className="space-y-2">
        <Label>项目类型</Label>
        <div className="grid grid-cols-3 gap-3">
          {PROJECT_TYPES.map((pt) => (
            <button
              key={pt.value}
              type="button"
              onClick={() => setProjectType(pt.value)}
              className={`flex flex-col items-center gap-2 p-4 rounded-lg border-2 transition-colors ${
                projectType === pt.value
                  ? "border-primary bg-primary/5"
                  : "border-border hover:border-foreground/20"
              }`}
            >
              <span className="text-2xl">{pt.icon}</span>
              <span className="text-xs font-medium">{pt.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="name">项目名称</Label>
        <Input
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：数据结构课程设计"
          required
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="desc">项目描述（可选）</Label>
        <Textarea
          id="desc"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="简要描述项目需求..."
          rows={3}
        />
      </div>

      <Button
        type="submit"
        disabled={!name.trim() || createMutation.isPending}
        className="w-full"
      >
        {createMutation.isPending && (
          <Loader2 className="h-4 w-4 animate-spin mr-2" />
        )}
        创建项目
      </Button>
    </form>
  );
}
