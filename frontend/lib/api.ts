import type {
  Category,
  CategoriesListResponse,
  Product,
  ProductsListResponse,
} from "./types";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export const CATALOG_PER_PAGE = 10;

export type ProductsResult = {
  items: Product[];
  total: number;
};

export async function getProducts(
  page = 1,
  perPage = CATALOG_PER_PAGE,
  category?: string,
): Promise<ProductsResult> {
  try {
    const params = new URLSearchParams({
      page: String(page),
      per_page: String(perPage),
    });
    if (category) {
      params.set("category", category);
    }
    const url = `${BACKEND_URL}/api/v1/product/?${params.toString()}`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      console.error(`getProducts: backend responded ${res.status}`);
      return { items: [], total: 0 };
    }
    const data = (await res.json()) as ProductsListResponse;
    return { items: data.payload ?? [], total: data.meta?.total ?? 0 };
  } catch (err) {
    console.error("getProducts: fetch failed", err);
    return { items: [], total: 0 };
  }
}

export async function getCategories(): Promise<Category[]> {
  try {
    const url = `${BACKEND_URL}/api/v1/category/`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      console.error(`getCategories: backend responded ${res.status}`);
      return [];
    }
    const data = (await res.json()) as CategoriesListResponse;
    return data.payload ?? [];
  } catch (err) {
    console.error("getCategories: fetch failed", err);
    return [];
  }
}
