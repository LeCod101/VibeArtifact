/**
 * 旧版 /projects/[id] 兼容：永久重定向到新工作区路由 /project/[id]
 */
import { redirect } from "next/navigation";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function LegacyProjectsIdRedirect({ params }: PageProps) {
  const { id } = await params;
  redirect(`/project/${id}`);
}
