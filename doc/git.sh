# Comandos BASH Linux
sudo systemctl list-units --type=service --state=running
sudo systemctl status <service.name>

# Verificar y eliminar __pycache__ de un repositorio
find . -type d -name "__pycache__"
find . -type d -name "__pycache__" -exec rm -rf {} +

# Copiar rutas de subcarpetas
find /home/jose/Documentos/core/17.0/gcaceres93 -mindepth 1 -maxdepth 1 -type d | xclip -selection clipboard
find /home/jose/Documentos/core/17.0/OCA -mindepth 1 -maxdepth 1 -type d | xclip -selection clipboard

# Filtra archivos que contengan el patron indicado (cualquier modelo)
grep -rn --include="*.py" "no_ver_factura_recibo = fields." .

rg -t py -n -C 3 "_(name|inherit)\s*=\s*['\"]hr\.payslip\.worked_days['\"]" .

# Para buscar attrs con patrones
rg -g "*.py" -e '^\s*(no_ver_factura_recibo)\s*=\s*fields\.' .

# Buscar dentro de múltiples archivos y mostrar contexto (3 líneas antes y después)
grep -rn --color=always -C 3 "def format_num(" .

# Filtra archivos que contengan los patrones al mismo tiempo and (un modelo en concreto)
grep -rl --include="*.py" 'def compute_sheet' . \
| xargs grep -lE "_(name|inherit)\s*=\s*['\"]hr.payslip['\"]" \
| xargs grep -rn --color=always -C 3 -e 'def compute_sheet' -e 'hr.payslip'

rg -t py --files-with-matches "def compute_sheet" . \
| xargs rg -t py --files-with-matches "_(name|inherit)\s*=\s*['\"]hr\.payslip['\"]" \
| xargs rg -t py -n -C 3 -e "def compute_sheet" -e "hr\.payslip"

rg -t py --files-with-matches "def action_approve()" . \
| xargs rg -t py --files-with-matches "_(name|inherit)\s*=\s*['\"]hr\.leave['\"]" \
| xargs rg -t py -n -H -C 3 -e "def action_approve()" -e "hr\.payslip"
