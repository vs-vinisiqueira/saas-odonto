import * as React from "react";

import { cn } from "@/lib/utils";

/** Área rolável simples (overflow nativo estilizado). */
export const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("overflow-y-auto [scrollbar-width:thin]", className)}
    {...props}
  />
));
ScrollArea.displayName = "ScrollArea";
