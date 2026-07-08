# Frontend Mobile — Memoization & Performance

> **Couche** : `10-frontend-mobile`  
> **Lié** : `00-core-principles/performance-first.md`

## Règles

- `React.memo` sur listes transactions (historique wallet).
- `useCallback` / `useMemo` pour handlers OTP et polling intervals.
- Éviter re-render sur balance FCFA pendant polling MoMo.

```json
{
  "heavy_lists": ["wallet transactions", "kyc liveness preview thumbnails"],
  "avoid": ["will-change abuse on scroll decorations", "matrix animations on lists"]
}
```
