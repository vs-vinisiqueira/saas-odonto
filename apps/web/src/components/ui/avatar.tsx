import { cn } from "@/lib/utils";

/** Avatar simples baseado em iniciais (sem imagem por enquanto). */
export function Avatar({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const initials = name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

  return (
    <span
      className={cn(
        "flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
        "bg-accent text-sm font-medium text-accent-foreground",
        className,
      )}
    >
      {initials || "?"}
    </span>
  );
}
