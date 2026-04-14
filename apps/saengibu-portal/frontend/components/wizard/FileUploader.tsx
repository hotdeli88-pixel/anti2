"use client";

import { cn } from "@/lib/cn";
import { Upload, X, File as FileIcon } from "lucide-react";
import { useCallback, useRef, useState } from "react";

interface FileUploaderProps {
  accept?: string[];
  maxSizeMB?: number;
  maxFiles?: number;
  onFilesChange?: (files: File[]) => void;
}

const DEFAULT_ACCEPT = [".hwp", ".hwpx", ".doc", ".docx", ".pdf"];

export function FileUploader({
  accept = DEFAULT_ACCEPT,
  maxSizeMB = 10,
  maxFiles = 3,
  onFilesChange,
}: FileUploaderProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (incoming: File[]): File[] => {
    const maxBytes = maxSizeMB * 1024 * 1024;
    const filtered: File[] = [];
    for (const f of incoming) {
      const ext = "." + f.name.split(".").pop()?.toLowerCase();
      if (!accept.includes(ext)) {
        setError(`지원하지 않는 파일 형식입니다: ${f.name} (허용: ${accept.join(", ")})`);
        continue;
      }
      if (f.size > maxBytes) {
        setError(`파일이 너무 큽니다: ${f.name} (${(f.size / 1024 / 1024).toFixed(1)}MB > ${maxSizeMB}MB)`);
        continue;
      }
      filtered.push(f);
    }
    return filtered.slice(0, Math.max(0, maxFiles - files.length));
  };

  const addFiles = useCallback(
    (incoming: FileList | File[]) => {
      setError(null);
      const validated = validate(Array.from(incoming));
      if (!validated.length) return;
      const next = [...files, ...validated].slice(0, maxFiles);
      setFiles(next);
      onFilesChange?.(next);
    },
    [files, maxFiles, onFilesChange],
  );

  const remove = (idx: number) => {
    const next = files.filter((_, i) => i !== idx);
    setFiles(next);
    onFilesChange?.(next);
  };

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        className={cn(
          "cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors duration-quick",
          dragOver
            ? "border-brand bg-brand-light"
            : "border-surface-border bg-surface-body hover:border-brand hover:bg-brand-light/30",
        )}
        role="button"
        tabIndex={0}
        aria-label="파일 업로드"
      >
        <Upload className="mx-auto mb-3 h-6 w-6 text-ink-gray" />
        <p className="text-body font-medium text-ink-dark">
          파일을 드래그하거나 클릭하여 업로드
        </p>
        <p className="mt-1 text-caption text-ink-light">
          {accept.join(", ")} · 파일당 {maxSizeMB}MB 이내 · 최대 {maxFiles}개
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept.join(",")}
          className="hidden"
          onChange={(e) => e.target.files && addFiles(e.target.files)}
        />
      </div>
      {error && (
        <p className="mt-2 text-body-sm text-danger" role="alert">
          {error}
        </p>
      )}
      {files.length > 0 && (
        <ul className="mt-3 space-y-2">
          {files.map((f, idx) => (
            <li
              key={idx}
              className="flex items-center justify-between rounded-md border border-surface-border bg-white px-3 py-2"
            >
              <span className="flex items-center gap-2 text-body-sm">
                <FileIcon className="h-4 w-4 text-ink-gray" />
                <span className="truncate max-w-[280px]">{f.name}</span>
                <span className="text-caption text-ink-light">
                  ({(f.size / 1024).toFixed(0)} KB)
                </span>
              </span>
              <button
                type="button"
                onClick={() => remove(idx)}
                className="text-ink-light hover:text-danger"
                aria-label={`${f.name} 삭제`}
              >
                <X className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-caption text-ink-light">
        업로드된 파일은 AI 피드백 참고용 맥락으로만 사용되며, 외부 서비스로 전송되지 않습니다.
      </p>
    </div>
  );
}
