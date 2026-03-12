/**
 * 新建对话弹窗组件
 *
 * 包含标题（可选）表单字段。
 */
"use client";

import { useState, type FormEvent } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { useLocale } from "@/i18n/context";
import t from "@/i18n/translations";
import type { Locale } from "@/i18n/translations";
import { useCreateConversationMutation } from "@/features/chat/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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

interface CreateConversationDialogProps {
  projectId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** 创建成功后的回调，传入新对话 ID */
  onCreated?: (conversationId: string) => void;
}

export function CreateConversationDialog({
  projectId,
  open,
  onOpenChange,
  onCreated,
}: CreateConversationDialogProps) {
  const { locale } = useLocale();
  const createMutation = useCreateConversationMutation(projectId);
  const [title, setTitle] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();

    try {
      const conv = await createMutation.mutateAsync({
        title: title || undefined,
      });
      toast.success(L(t.project.createConversationSuccess, locale));
      onOpenChange(false);
      setTitle("");
      onCreated?.(conv.id);
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
          <DialogTitle>{L(t.project.newConversation, locale)}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="convTitle">
              {L(t.project.conversationTitle, locale)}
            </Label>
            <Input
              id="convTitle"
              placeholder={L(t.project.conversationPlaceholder, locale)}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
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
