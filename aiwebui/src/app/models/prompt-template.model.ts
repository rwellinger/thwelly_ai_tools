export interface PromptTemplate {
  id: number;
  category: string;
  action: string;
  pre_condition: string;
  post_condition: string;
  description?: string;
  version?: string;
  model_hint?: string;
  active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface PromptTemplateUpdate {
  pre_condition?: string;
  post_condition?: string;
  description?: string;
}

export interface PromptTemplatesResponse {
  categories: Record<string, Record<string, PromptTemplate>>;
}

export interface PromptCategoryResponse {
  category: string;
  templates: Record<string, PromptTemplate>;
}