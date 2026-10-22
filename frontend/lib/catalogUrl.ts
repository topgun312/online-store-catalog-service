type CatalogQuery = {
  category?: string;
  page?: number;
};

export function buildCatalogUrl({ category, page }: CatalogQuery): string {
  const params = new URLSearchParams();
  if (category) {
    params.set("category", category);
  }
  if (page && page > 1) {
    params.set("page", String(page));
  }
  const query = params.toString();
  return query ? `/?${query}` : "/";
}
