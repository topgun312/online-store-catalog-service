import Link from "next/link";
import type { Category } from "@/lib/types";
import { buildCatalogUrl } from "@/lib/catalogUrl";

type CategoryFilterProps = {
  categories: Category[];
  activeCategory?: string;
};

export default function CategoryFilter({
  categories,
  activeCategory,
}: CategoryFilterProps) {
  if (categories.length === 0) {
    return null;
  }

  return (
    <nav className="category-filter" aria-label="Фильтр по категориям">
      <Link
        href={buildCatalogUrl({})}
        className={`category-chip${!activeCategory ? " category-chip--active" : ""}`}
        aria-current={!activeCategory ? "page" : undefined}
      >
        Все
      </Link>
      {categories.map((category) => {
        const isActive =
          category.slug === activeCategory || category.id === activeCategory;
        return (
          <Link
            key={category.id}
            href={buildCatalogUrl({ category: category.slug })}
            className={`category-chip${isActive ? " category-chip--active" : ""}`}
            aria-current={isActive ? "page" : undefined}
          >
            {category.name}
          </Link>
        );
      })}
    </nav>
  );
}
