{ self, ... }:
{
  config,
  lib,
  pkgs,
  ...
}:

let
  serviceName = "pm-insight";
  runtimePath = "/run/${serviceName}";
  package = self.packages.${pkgs.system}.pm-insight;
  user = "sv_pm-insight";

  cfg = config.services.pm-insight;
in
{
  options = {
    services.pm-insight = {
      enable = lib.mkEnableOption ''
        Whether to enable pm-insight services
      '';

      production = lib.mkEnableOption ''
        Wheter to enable production mode or fallback to dev mode
      '';

      domainName = lib.mkOption {
        type = lib.types.str;
        description = ''
          Domain Name for the service
        '';
      };

      httpAddress = lib.mkOption {
        type = lib.types.str;
        description = ''
          HTTP address for the pm-insight service
        '';
      };

      httpPort = lib.mkOption {
        type = lib.types.int;
        description = ''
          HTTP port for the pm-insight service
        '';
      };

      maxUploadSize = lib.mkOption {
        type = lib.types.int;
        default = 200;
        description = ''
          Max Upload size for the pm-insight service in GB
        '';
      };

    };
  };

  config = lib.mkIf cfg.enable {

    systemd.services.${serviceName} = {
      description = "PM Insight service";
      before = [ "nginx.service" ];
      wantedBy = [ "multi-user.target" ];

      path = [ package ];

      environment = {
        PM_INSIGHT_DOCS_DIR = "${package}/docs";

        STREAMLIT_SERVER_ADDRESS = cfg.httpAddress;
        STREAMLIT_SERVER_PORT = toString cfg.httpPort;
        STREAMLIT_SERVER_MAX_UPLOAD_SIZE = toString cfg.maxUploadSize;
        STREAMLIT_SERVER_ENABLE_CORS = "true";
        STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION = "true";
        STREAMLIT_SERVER_HEADLESS = "true";
        STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false";
        STREAMLIT_SERVER_FILE_WATCHER_TYPE = "none";
        STREAMLIT_CLIENT_TOOLBAR_MODE = "minimal";
      };

      script = ''
        pm-insight
      '';

      serviceConfig = {
        Group = config.services.nginx.group;
        User = user;

        CacheDirectory = [
          serviceName
          "fontconfig
"
        ];
        RuntimeDirectory = serviceName;
        RuntimeDirectoryMode = 750;

        WorkingDirectory = runtimePath;
      };
    };

    # "https://discuss.streamlit.io/t/streamlit-docker-nginx-ssl-https/2195/3"
    # "https://discuss.streamlit.io/t/accessing-streamlit-through-reverse-proxy-results-in-please-wait-solved/8618"
    services.nginx.virtualHosts."${cfg.domainName}" = {
      enableACME = cfg.production;
      forceSSL = cfg.production;

      extraConfig = ''
        access_log /var/log/nginx/${cfg.domainName}.access.log json_analytics;
        error_log /var/log/nginx/${cfg.domainName}.error.log;
      '';

      locations."/" = {
        proxyPass = "http://${cfg.httpAddress}:${toString cfg.httpPort}/";
        proxyWebsockets = true;
        recommendedProxySettings = true;
      };

      locations."/stream" = {
        proxyPass = "http://${cfg.httpAddress}:${toString cfg.httpPort}/stream";
        proxyWebsockets = true;
        recommendedProxySettings = true;
      };

    };

    users.users.${user} = {
      description = "pm-insight backend service user";
      group = "nogroup";
      isSystemUser = true;
    };
  };
}
