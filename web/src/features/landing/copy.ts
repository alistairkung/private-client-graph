import { useLocale } from "../../shared/locale";
const en = {
  research: "Research",
  enter: "Open practitioner prototype",
  explore: "Explore the example",
  language: "Language",
  headline: "Build the structure.\nKeep the Evidence.",
  intro:
    "AI-assisted trust structure building, with the words behind every proposed relationship.",
  description:
    "Turn synthetic source material into a structure you can inspect. Trace each connection to exact Evidence, then make your own decision.",
  boundary:
    "Synthetic or fictional material only. Do not upload real client or personal information.",
  example: "Explore the synthetic example",
  curated: "Curated synthetic example",
  curatedNote:
    "A curated synthetic example, not live analysis or a measured model result.",
  source: "Source fragment",
  sourceExcerpts: "Source excerpts",
  evidence: "Exact supporting Evidence",
  diagram: "Family and trust relationships",
  choose: "Choose a relationship to follow its Evidence.",
  loading: "Loading the synthetic example…",
  error:
    "The example could not be loaded. You can try again or open the full public demo.",
  retry: "Try again",
  fullDemo: "Explore public Matters",
  noClaims: "No relationships are available in this example.",
  missing:
    "The exact Evidence could not be located. Open the full demo to inspect the source.",
  acceptance: "A proposal is a starting point.\nAcceptance is your decision.",
  acceptanceBody:
    "The practitioner prototype puts the proposed relationships beside their Evidence. Review the complete proposal, then explicitly confirm or discard it.",
  acceptanceNote:
    "A highlighted passage supports a claim. It does not replace professional judgement.",
  read: "Read",
  inspect: "Inspect",
  decide: "Decide",
  readText: "Begin with the source material.",
  inspectText: "Trace proposed claims to exact Evidence.",
  decideText: "Accept or discard the whole proposal explicitly.",
  researchTitle: "The proof belongs\nin the open.",
  researchBody:
    "Explore the published research and the public demonstration. Curated examples explain the review experience; research results describe evaluated model behaviour.",
  researchLink: "Read the research results",
  researchNote:
    "This prototype is limited to synthetic and fictional material. Authentication in the practitioner prototype does not make it suitable for real client data.",
  closing: "See the relationship.\nRead the reason.",
  footer: "Private Client Graph",
  footerNote: "An Evidence-led research prototype.",
  active: "Selected relationship",
  locator: "Evidence identifier",
  exampleSource: "Source",
};
type Copy = typeof en;
const zh: Copy = {
  research: "研究",
  enter: "打开实务原型",
  explore: "探索示例",
  language: "语言",
  headline: "构建关系结构。\n保留支持证据。",
  intro: "由 AI 辅助构建信托关系结构，保留每项提议关系的原文依据。",
  description:
    "以证据为依据的工作空间，用于审阅私人客户事务中的家庭与信托关系。",
  boundary: "仅限合成或虚构资料。请勿上传真实客户或个人信息。",
  example: "探索合成示例",
  curated: "精选合成示例",
  curatedNote: "由后端提供的理想示例，并非实时分析或模型评测结果。",
  source: "来源片段",
  sourceExcerpts: "来源摘录",
  evidence: "确切支持证据",
  diagram: "家庭与信托关系",
  choose: "选择一项关系，追溯其支持证据。",
  loading: "正在加载合成示例…",
  error: "无法加载示例。请重试或打开完整公开演示。",
  retry: "重试",
  fullDemo: "浏览公开事项",
  noClaims: "此示例没有可用关系。",
  missing: "无法定位确切证据。请打开完整演示以核查来源。",
  acceptance: "提案是起点。\n是否接受，由您决定。",
  acceptanceBody:
    "实务原型将提议的关系与支持证据并列显示。审阅完整提案后，明确选择确认或丢弃。",
  acceptanceNote: "高亮段落为主张提供支持，但不能替代专业判断。",
  read: "阅读",
  inspect: "核查",
  decide: "决定",
  readText: "从来源资料开始。",
  inspectText: "将提议的关系追溯至确切证据。",
  decideText: "明确接受或丢弃整个提案。",
  researchTitle: "研究依据，\n公开可查。",
  researchBody:
    "探索已发表的研究和公开演示。精选示例用于说明审阅体验；研究结果则说明经过评测的模型表现。",
  researchLink: "阅读研究结果",
  researchNote:
    "本原型仅限合成与虚构资料。实务原型中的身份验证并不意味着其适用于真实客户数据。",
  closing: "看清关系。\n读懂依据。",
  footer: "Private Client Graph",
  footerNote: "以证据为依据的研究原型。",
  active: "所选关系",
  locator: "证据标识",
  exampleSource: "来源",
};
export function useLandingCopy() {
  const { locale } = useLocale();
  return locale === "zh-CN" ? zh : en;
}
export const relationshipWords = {
  en: {
    parent_of: "parent of",
    spouse_of: "spouse of",
    sibling_of: "sibling of",
    settlor_of: "settlor of",
    trustee_of: "trustee of",
    beneficiary_of: "beneficiary of",
  },
  "zh-CN": {
    parent_of: "父母",
    spouse_of: "配偶",
    sibling_of: "手足",
    settlor_of: "设立人",
    trustee_of: "受托人",
    beneficiary_of: "受益人",
  },
};
