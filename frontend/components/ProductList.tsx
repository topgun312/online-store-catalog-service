import type { Product } from "@/lib/types";
import ProductCard from "./ProductCard";

export default function ProductList({ items }: { items: Product[] }) {
  if (items.length === 0) {
    return <p className="empty">Товаров пока нет</p>;
  }

  return (
    <ul className="product-grid">
      {items.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </ul>
  );
}
