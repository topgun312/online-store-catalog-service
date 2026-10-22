import Link from "next/link";
import { buildCatalogUrl } from "@/lib/catalogUrl";

type PaginationProps = {
  page: number;
  totalPages: number;
  category?: string;
};

export default function Pagination({
  page,
  totalPages,
  category,
}: PaginationProps) {
  if (totalPages <= 1) {
    return null;
  }

  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  return (
    <nav className="pagination" aria-label="Пагинация">
      {hasPrev ? (
        <Link
          href={buildCatalogUrl({ category, page: page - 1 })}
          className="pagination-button"
          rel="prev"
        >
          ← Назад
        </Link>
      ) : (
        <span className="pagination-button pagination-button--disabled">
          ← Назад
        </span>
      )}

      <span className="pagination-info">
        Страница {page} из {totalPages}
      </span>

      {hasNext ? (
        <Link
          href={buildCatalogUrl({ category, page: page + 1 })}
          className="pagination-button"
          rel="next"
        >
          Вперёд →
        </Link>
      ) : (
        <span className="pagination-button pagination-button--disabled">
          Вперёд →
        </span>
      )}
    </nav>
  );
}
