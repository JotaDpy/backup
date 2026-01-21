# Para usar en tu máquian local
BASE="/odoo/custom"
direcciones=(
account_payment
accounting_reports_paraguay
facturacion_electronica
fondoestrella
hr_paraguay
odoo_paraguay
tesaka
)

archivo="/tmp/estado_repos_$(date '+%Y%m%d_%H%M%S').csv"

{
  echo 'RUTA,BRANCH,FECHA,AUTOR,COMMIT_HASH,COMMIT_MESSAGE'
  for dir in "${direcciones[@]}"; do
    ruta="$BASE/$dir"
    [ -d "$ruta/.git" ] || continue

    branch=$(git -C "$ruta" branch --show-current)
    git -C "$ruta" log -1 \
      --date=short \
      --pretty=format:"\"$ruta\",\"$branch\",\"%cd\",\"%an\",\"%h\",\"%s\""
    echo
  done
} > "$archivo"

echo "CSV generado en: $archivo"

# Para usar en tu máquian local
BASE="/odoo/custom/oca"
direcciones=(
account-financial-reporting
operating-unit
reporting-engine
server-ux

)

archivo="/tmp/estado_repos_$(date '+%Y%m%d_%H%M%S').csv"

{
  echo 'RUTA,BRANCH,FECHA,AUTOR,COMMIT_HASH,COMMIT_MESSAGE'
  for dir in "${direcciones[@]}"; do
    ruta="$BASE/$dir"
    [ -d "$ruta/.git" ] || continue

    branch=$(git -C "$ruta" branch --show-current)
    git -C "$ruta" log -1 \
      --date=short \
      --pretty=format:"\"$ruta\",\"$branch\",\"%cd\",\"%an\",\"%h\",\"%s\""
    echo
  done
} > "$archivo"

echo "CSV generado en: $archivo"
