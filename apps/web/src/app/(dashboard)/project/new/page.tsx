/**
 * 新建项目页面
 */
import { CreateProjectForm } from "@/features/project/components/create-project-form";

export default function NewProjectPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-8 md:py-12">
      <h1 className="text-2xl font-bold mb-2">新建项目</h1>
      <p className="text-sm text-muted-foreground mb-8">
        选择项目类型，开始你的 AI 辅助开发之旅
      </p>
      <CreateProjectForm />
    </div>
  );
}
