export type Locale = "en" | "zh-CN";
export type LocalizedText = Readonly<Record<Locale, string>>;

export const FPS = 30;
export const DURATION_SECONDS = 84;
export const TOTAL_FRAMES = FPS * DURATION_SECONDS;

export const scopeBadge: LocalizedText = {
  en: "Synthetic workflow demonstration",
  "zh-CN": "合成资料流程演示",
};

export const fixtureNotice: LocalizedText = {
  en: "Local fixture analysis · timing edited",
  "zh-CN": "本地预设分析结果 · 时长经剪辑",
};

export const evidenceQuotes = {
  trustee: "Morgan Example is trustee of the Fictional Trust.",
  parent: "Alice Example is the parent of Ben Example.",
} as const;

export type CaptureKey =
  | "ledger"
  | "intake-empty"
  | "intake-reference"
  | "intake-title"
  | "intake-files"
  | "proposal"
  | "selected-trustee"
  | "source-trustee"
  | "confirmation"
  | "accepted"
  | "ledger-saved"
  | "reopened-parent";

/** Cue timing is in seconds relative to the start of its shot. */
export type CaptionCue = {
  from: number;
  duration: number;
  text: LocalizedText;
};

/** Capture keys are shared; the renderer chooses the localized capture folder. */
export type Shot = {
  id: string;
  from: number;
  duration: number;
  image: CaptureKey;
  title: LocalizedText;
  cues: readonly CaptionCue[];
  quote?: string;
  source?: LocalizedText;
  kind?: "screen" | "close";
};

export const shots: readonly Shot[] = [
  {
    id: "start",
    from: 0,
    duration: 6,
    image: "ledger",
    title: {
      en: "Let’s create a reviewable Matter",
      "zh-CN": "一起创建可审阅的事项",
    },
    cues: [
      {
        from: 0,
        duration: 6,
        text: {
          en: "We’re already signed in to the practitioner workspace.",
          "zh-CN": "现在已登录专业人员工作区。",
        },
      },
    ],
  },
  {
    id: "create",
    from: 6,
    duration: 4,
    image: "intake-empty",
    title: { en: "Start with your documents", "zh-CN": "从文档开始" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Choose Create Matter to begin a new intake.",
          "zh-CN": "点击“创建事项”，开始导入资料。",
        },
      },
    ],
  },
  {
    id: "reference",
    from: 10,
    duration: 4,
    image: "intake-reference",
    title: { en: "Use your existing reference", "zh-CN": "沿用现有编号" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Enter the reference from your existing Matter system.",
          "zh-CN": "填写现有事项系统中的编号。",
        },
      },
    ],
  },
  {
    id: "name",
    from: 14,
    duration: 4,
    image: "intake-title",
    title: { en: "Give this Matter a name", "zh-CN": "为事项命名" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "A clear title makes it easy to find again.",
          "zh-CN": "清晰的名称，方便日后查找。",
        },
      },
    ],
  },
  {
    id: "documents",
    from: 18,
    duration: 8,
    image: "intake-files",
    title: { en: "Bring the documents together", "zh-CN": "把文档放在一起" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Select two PDFs and give each Source a title.",
          "zh-CN": "选择两份 PDF，分别填写来源标题。",
        },
      },
      {
        from: 4,
        duration: 4,
        text: {
          en: "Confirm that these documents contain only fictional material.",
          "zh-CN": "确认文档仅包含虚构资料。",
        },
      },
    ],
  },
  {
    id: "analyse",
    from: 26,
    duration: 4,
    image: "intake-files",
    title: { en: "Prepare one proposal", "zh-CN": "生成一份提案" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Choose Upload and analyse. We’ll review the proposal next.",
          "zh-CN": "点击“上传并分析”，接下来审阅提案。",
        },
      },
    ],
  },
  {
    id: "proposal",
    from: 30,
    duration: 8,
    image: "proposal",
    title: { en: "Saved for your review", "zh-CN": "提案已保存，等待审阅" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "These relationships are proposed. No Matter has been created yet.",
          "zh-CN": "这些关系仍是提案，尚未创建事项。",
        },
      },
      {
        from: 4,
        duration: 4,
        text: {
          en: "You can return to this saved proposal from Matters.",
          "zh-CN": "可随时从事项列表返回这份已保存的提案。",
        },
      },
    ],
  },
  {
    id: "relationship",
    from: 38,
    duration: 9,
    image: "selected-trustee",
    title: { en: "Select the relationship", "zh-CN": "选中要审阅的关系" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Let’s check Morgan’s trustee role in the Fictional Trust.",
          "zh-CN": "查看 Morgan 在 Fictional Trust 中的受托人关系。",
        },
      },
      {
        from: 4,
        duration: 5,
        text: {
          en: "The supporting evidence identifies Source 2.",
          "zh-CN": "支持这条关系的证据来自来源 2。",
        },
      },
    ],
  },
  {
    id: "source",
    from: 47,
    duration: 9,
    image: "source-trustee",
    title: { en: "Check the original words", "zh-CN": "核对原文" },
    cues: [
      {
        from: 0,
        duration: 9,
        text: {
          en: "View in source takes us to the exact supporting passage.",
          "zh-CN": "点击“在来源中查看”，定位到支持这条关系的原文。",
        },
      },
    ],
    quote: evidenceQuotes.trustee,
    source: { en: "Source 2 · exact quotation", "zh-CN": "来源 2 · 原文引文" },
  },
  {
    id: "confirm",
    from: 56,
    duration: 8,
    image: "confirmation",
    title: {
      en: "You decide what becomes accepted",
      "zh-CN": "由你决定是否确认",
    },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Review the whole proposal before confirming.",
          "zh-CN": "确认前，请审阅完整提案。",
        },
      },
      {
        from: 4,
        duration: 4,
        text: {
          en: "Confirm and create Matter accepts all relationships and supplied Sources.",
          "zh-CN": "点击“确认并创建事项”，接受整份关系提案及所有来源。",
        },
      },
    ],
  },
  {
    id: "accepted",
    from: 64,
    duration: 6,
    image: "accepted",
    title: { en: "Your Matter is now saved", "zh-CN": "事项已创建并保存" },
    cues: [
      {
        from: 0,
        duration: 6,
        text: {
          en: "Your reviewed relationships and source evidence are saved together.",
          "zh-CN": "审阅后的关系与来源证据一并保存。",
        },
      },
    ],
  },
  {
    id: "return",
    from: 70,
    duration: 4,
    image: "ledger-saved",
    title: { en: "Come back to it", "zh-CN": "随时回来查看" },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Back to Matters. Open the accepted Matter from the list.",
          "zh-CN": "返回事项列表，重新打开已接受的事项。",
        },
      },
    ],
  },
  {
    id: "reopen",
    from: 74,
    duration: 6,
    image: "reopened-parent",
    title: { en: "The evidence is still there", "zh-CN": "证据仍可追溯" },
    cues: [
      {
        from: 0,
        duration: 6,
        text: {
          en: "Alice’s parent relationship takes us back to Source 1.",
          "zh-CN": "选中 Alice 的亲子关系，再次查看来源 1。",
        },
      },
    ],
    quote: evidenceQuotes.parent,
    source: { en: "Source 1 · exact quotation", "zh-CN": "来源 1 · 原文引文" },
  },
  {
    id: "close",
    from: 80,
    duration: 4,
    image: "reopened-parent",
    kind: "close",
    title: {
      en: "A Matter you can return to",
      "zh-CN": "让每个事项都有据可查",
    },
    cues: [
      {
        from: 0,
        duration: 4,
        text: {
          en: "Documents. Relationships. Evidence. Your review.",
          "zh-CN": "文档、关系、证据，由你审阅。",
        },
      },
    ],
  },
];
