/* Displayed SQL and executed SQL share these exact query strings.
   The defective query carries two rule mismatches: `>` where the rule says
   "at least" (line 7), and no clause collapsing repeated order IDs. The
   correction changes the operator and adds GROUP BY order_id; nothing else
   differs (decision record D14). */
(() => {
  const buggy = `WITH eligible_orders AS (
    SELECT
        order_id
    FROM dispatch_orders
    WHERE paid = 1
      AND shipped = 0
      AND age_hours > 48
      AND canceled = 0
)
SELECT order_id
FROM eligible_orders
ORDER BY order_id;`;
  const fixed = buggy
    .replace('age_hours > 48', 'age_hours >= 48')
    .replace('FROM eligible_orders\nORDER BY order_id;', 'FROM eligible_orders\nGROUP BY order_id\nORDER BY order_id;');
  globalThis.DispatchExample=Object.freeze({buggy,fixed});
})();
