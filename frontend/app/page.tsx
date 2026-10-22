import { redirect } from "next/navigation";
import CategoryFilter from "@/components/CategoryFilter";
import Pagination from "@/components/Pagination";
import ProductList from "@/components/ProductList";
import { CATALOG_PER_PAGE, getCategories, getProducts } from "@/lib/api";
import { buildCatalogUrl } from "@/lib/catalogUrl";

export const dynamic = "force-dynamic";

type HomeProps = {
  searchParams: Promise<{
    category?: string | string[];
    page?: string | string[];
  }>;
};

function firstValue(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export default async function Home({ searchParams }: HomeProps) {
  const params = await searchParams;

  const category = firstValue(params.category)?.trim() || undefined;
  const parsedPage = Number.parseInt(firstValue(params.page) ?? "1", 10);
  const page = Number.isFinite(parsedPage) && parsedPage > 0 ? parsedPage : 1;

  const [{ items, total }, categories] = await Promise.all([
    getProducts(page, CATALOG_PER_PAGE, category),
    getCategories(),
  ]);

  const totalPages = Math.max(1, Math.ceil(total / CATALOG_PER_PAGE));
  if (page > totalPages) {
    redirect(buildCatalogUrl({ category, page: totalPages }));
  }

  return (
    <main className="catalog">
      <p className="site-title">Интернет-магазин</p>
      <h1>Каталог</h1>
      <CategoryFilter categories={categories} activeCategory={category} />
      <ProductList items={items} />
      <Pagination page={page} totalPages={totalPages} category={category} />
    </main>
  );
}
