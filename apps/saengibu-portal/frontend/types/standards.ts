export type Scale = "5grade" | "3grade" | "P/F";
export type Level = "A" | "B" | "C" | "D" | "E" | "P" | "F";
export type SchoolLevel = "elem" | "middle" | "high";

export interface AchievementLevel {
  level: Level;
  scale: Scale;
  descriptor: string;
  order_index: number;
  cutline_hint?: string | null;
}

export interface AchievementStandard {
  id: number;
  curriculum: string;
  school_level: SchoolLevel;
  grade: number;
  subject_code: string;
  domain?: string | null;
  domain_code?: string | null;
  unit_code?: string | null;
  unit_title?: string | null;
  code: string;
  statement: string;
  eval_scale: Scale;
  min_achievement?: Level | null;
  rules_version: string;
  levels: AchievementLevel[];
}

export interface StandardsListPage {
  items: AchievementStandard[];
  next_cursor?: string | null;
}

export interface DomainLevel {
  id: number;
  curriculum: string;
  school_level: SchoolLevel;
  grade: number;
  subject_code: string;
  domain: string;
  level: Level;
  descriptor: string;
}

export interface CurriculumMatrixEntry {
  curriculum: string;
  school_level: SchoolLevel;
  grade: number;
  subject_code: string;
  standard_count: number;
  level_count: number;
}
