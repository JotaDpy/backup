"""
Definiciones de tipos para scripts de Odoo
Colocar en: /home/jose/Documentos/clientes/17KEEPER/backup/python/odoo_types.py
"""

# Definición básica para que VS Code reconozca 'env'
class OdooEnvironment:
    """Tipo básico para el environment de Odoo"""
    def __getitem__(self, model_name: str):
        """Permite env['model.name']"""
        return OdooModel()

class OdooModel:
    """Tipo básico para modelos de Odoo"""
    def search(self, domain, **kwargs):
        """Búsqueda de registros"""
        return OdooRecordSet()
    
    def browse(self, ids):
        """Obtener registros por ID"""
        return OdooRecordSet()

class OdooRecordSet:
    """Tipo básico para recordsets de Odoo"""
    def __iter__(self):
        return iter([])
    
    def __len__(self):
        return 0
    
    @property
    def ids(self):
        return []
    
    @property
    def name(self):
        return ""

# Variable global env que VS Code puede reconocer
env: OdooEnvironment