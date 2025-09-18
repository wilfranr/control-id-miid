"""
Definición de entornos para la aplicación.

Este archivo es generado/actualizado por la GUI.
"""

ACTIVE_ENV = "PROD"

ENVIRONMENTS = {
    "DEV": {
        "miid": {
            "host": "miidsqldev.mysql.database.azure.com",
            "port": 3306,
            "user": "Wilfran.Rivera",
            "password": "zi4i1WFBpRX8*Bytte",
            "database": "miidcore",
            "ec_id": 11000
        },
        "azure": {
            "servidor": "inspruebas.database.windows.net",
            "base_datos": "ByKeeper_Desarrollo",
            "usuario": "MonitorOp",
            "contraseña": "zi3i1WFBpRX8*Bytte",
            "stored_procedure": "dbo.GetMatchIDImgFaceByCASBid",
            "business_context": "MatchId"
        },
        "control_id": {
            "base_url": "http://10.8.0.2",
            "login": "admin",
            "password": "admin",
            "default_group_id": 1
        },
        "carpetas": {
            "carpeta_local_temp": "C:\\\\temp\\\\Imagenes_Dev",
            "extension_imagen": ".jpg"
        }
    },
    "PROD": {
        "miid": {
            "host": "miidsqlprod.mysql.database.azure.com",
            "port": 3306,
            "user": "Wilfran.Rivera",
            "password": "zi4i1WFBpRX8*Bytte",
            "database": "miidcore",
            "ec_id": 3000
        },
        "azure": {
            "servidor": "yi8s81p975.database.windows.net",
            "base_datos": "ByKeeper_Dev",
            "usuario": "MonitorOp",
            "contraseña": "4wL5E7ta5tr3*Bytte2025*",
            "stored_procedure": "dbo.GetMatchIDImgFaceByCASBId",
            "business_context": "MatchId"
        },
        "control_id": {
            "base_url": "http://10.8.0.3",
            "login": "admin",
            "password": "admin",
            "default_group_id": 1
        },
        "carpetas": {
            "carpeta_local_temp": "C:\\\\temp\\\\Imagenes_Prod",
            "extension_imagen": ".jpg"
        }
    }
}
