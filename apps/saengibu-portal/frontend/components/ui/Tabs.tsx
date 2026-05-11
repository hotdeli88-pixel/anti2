"use client";

import { cn } from "@/lib/cn";
import * as T from "@radix-ui/react-tabs";
import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";

export const Tabs = T.Root;

export const TabsList = forwardRef<
  ElementRef<typeof T.List>,
  ComponentPropsWithoutRef<typeof T.List>
>(({ className, ...props }, ref) => (
  <T.List
    ref={ref}
    className={cn(
      "flex gap-6 border-b-2 border-surface-border mb-6",
      className,
    )}
    {...props}
  />
));
TabsList.displayName = "TabsList";

export const TabsTrigger = forwardRef<
  ElementRef<typeof T.Trigger>,
  ComponentPropsWithoutRef<typeof T.Trigger>
>(({ className, ...props }, ref) => (
  <T.Trigger
    ref={ref}
    className={cn(
      "relative py-3 px-1 text-base font-semibold text-ink-gray hover:text-ink-dark cursor-pointer outline-none transition",
      "data-[state=active]:text-brand",
      "data-[state=active]:after:content-[''] data-[state=active]:after:absolute data-[state=active]:after:-bottom-[2px] data-[state=active]:after:left-0 data-[state=active]:after:w-full data-[state=active]:after:h-[3px] data-[state=active]:after:bg-brand data-[state=active]:after:rounded-t-[3px]",
      className,
    )}
    {...props}
  />
));
TabsTrigger.displayName = "TabsTrigger";

export const TabsContent = forwardRef<
  ElementRef<typeof T.Content>,
  ComponentPropsWithoutRef<typeof T.Content>
>(({ className, ...props }, ref) => (
  <T.Content
    ref={ref}
    className={cn(
      "outline-none data-[state=active]:animate-fade-in",
      className,
    )}
    {...props}
  />
));
TabsContent.displayName = "TabsContent";
