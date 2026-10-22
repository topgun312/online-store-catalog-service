import type { Product } from "@/lib/types";

export default function ProductCard({ product }: { product: Product }) {
  return (
    <li className="product-card">
      <img src={product.image_url} alt={product.title} loading="lazy" />
      <h3>{product.title}</h3>
    </li>
  );
}
