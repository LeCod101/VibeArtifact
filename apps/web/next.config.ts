import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * WebContainer 需要 Cross-Origin-Embedder-Policy 和 Cross-Origin-Opener-Policy 头。
   * 仅对项目工作区页面设置，避免影响其他页面的跨域资源加载。
   */
  async headers() {
    return [
      {
        source: "/project/:id*",
        headers: [
          {
            key: "Cross-Origin-Embedder-Policy",
            value: "require-corp",
          },
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
