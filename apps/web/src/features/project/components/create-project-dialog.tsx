/**
 * 新建项目弹窗组件
 *
 * 包含名称（必填）和描述（选填）两个表单字段。
 * 提交后自动刷新项目列表。
 */
"use client";

import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useCreateProjectMutation } from "@/features/project/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ApiError } from "@/lib/api-client/errors";

/** 多语言取值辅助函数 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function L(obj: { zh: any; en: any }, locale: Locale) {
  return obj[locale];
}

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateProjectDialog({
  open,
  onOpenChange,
}: CreateProjectDialogProps) {
  const { locale } = useLocale();
  const createMutation = useCreateProjectMutation();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      await createMutation.mutateAsync({
        name,
        description: description || undefined,
      });
      toast.success(L(t.project.createSuccess, locale));
      // 关闭弹窗并重置表单
      onOpenChange(false);
      setName("");
      setDescription("");
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.detail : L(t.common.error, locale);
      toast.error(msg);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{L(t.project.createTitle, locale)}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="projectName">{L(t.project.nameLabel, locale)}</Label>
            <Input
              id="projectName"
              placeholder={L(t.project.namePlaceholder, locale)}
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="projectDesc">{L(t.project.descLabel, locale)}</Label>
            <Textarea
              id="projectDesc"
              placeholder={L(t.project.descPlaceholder, locale)}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              {L(t.project.cancelBtn, locale)}
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              {L(t.project.createBtn, locale)}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
