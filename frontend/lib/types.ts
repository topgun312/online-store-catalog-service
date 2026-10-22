export type Product = {
  id: string;
  title: string;
  image_url: string;
  category_id?: string | null;
  category_name?: string | null;
  created_at: string;
};

export type Category = {
  id: string;
  name: string;
  slug: string;
};

export type PageMeta = {
  page: number;
  per_page: number;
  total: number;
};

export type ProductsListResponse = {
  payload: Product[];
  meta: PageMeta;
};

export type CategoriesListResponse = {
  payload: Category[];
};
