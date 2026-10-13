/* Displayed SQL and executed SQL share these exact query strings. */
(() => {
  const buggy = `WITH eligible_orders AS (
    SELECT
        order_id
    FROM dispatch_orders
    WHERE paid = 1
      AND shipped = 0
      AND age_hours > 48
      AND canceled = 0
),
unique_orders AS (
    SELECT DISTINCT order_id
    FROM eligible_orders
)
SELECT order_id FROM unique_orders
ORDER BY order_id;`;
  const fixed = buggy.replace('age_hours > 48', 'age_hours >= 48');
  globalThis.DispatchExample=Object.freeze({buggy,fixed});
})();
