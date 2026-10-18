export function Icon({
  name,
}: {
  name:
    | "atlas"
    | "arrow"
    | "plus"
    | "person"
    | "file"
    | "close"
    | "menu"
    | "search";
}) {
  const paths = {
    atlas: "M4 4h6l2 3 2-3h6v16h-6l-2-3-2 3H4V4Zm8 3v10",
    arrow: "M5 12h14m-6-6 6 6-6 6",
    plus: "M12 5v14M5 12h14",
    person: "M5 20c0-8 14-8 14 0M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
    file: "M6 3h8l4 4v14H6V3Zm8 0v5h4M9 12h6m-6 4h6",
    close: "m6 6 12 12M6 18 18 6",
    menu: "M4 6h16M4 12h16M4 18h16",
    search: "m16 16 5 5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z",
  };
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={paths[name]} />
    </svg>
  );
}
