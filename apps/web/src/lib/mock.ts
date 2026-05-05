export const projects = [
  {
    id: "project_demo_001",
    name: "新能源产业政策影响研究",
    status: "解析完成",
    documents: 3,
    policies: 18,
    updatedAt: "2026-05-05"
  },
  {
    id: "project_demo_002",
    name: "低空经济市场传导链扫描",
    status: "待分析",
    documents: 1,
    policies: 7,
    updatedAt: "2026-05-04"
  }
];

export const policies = [
  {
    id: "policy_demo_001",
    title: "示例产业政策原文",
    issuer: "Mock policy issuer",
    jurisdiction: "China",
    type: "industrial_policy",
    date: "2025-01-10",
    checksum: "11111111..."
  },
  {
    id: "policy_demo_002",
    title: "示例市场准入规则",
    issuer: "Mock regulator",
    jurisdiction: "EU",
    type: "market_access",
    date: "2024-11-18",
    checksum: "22222222..."
  }
];

export const providers = [
  "阿里云百炼 / 通义千问 / DashScope",
  "百度千帆 / 文心 / Qianfan",
  "腾讯混元 / Hunyuan",
  "火山方舟 / 豆包 / VolcArk",
  "智谱 AI / GLM / Zhipu",
  "DeepSeek",
  "Moonshot / Kimi",
  "MiniMax",
  "科大讯飞 / 星火 / Spark",
  "OpenAI-compatible Custom Provider",
  "Local Provider / Ollama / vLLM"
];
