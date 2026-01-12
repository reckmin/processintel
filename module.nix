{ self, ... }:
{
  config,
  lib,
  pkgs,
  ...
}:

let
  serviceName = "processintel";
  runtimePath = "/run/${serviceName}";
  package = self.packages.${pkgs.system}.processintel;
  user = "sv_processintel";

  cfg = config.services.processintel;
in
{
  options = {
    services.processintel = {
      enable = lib.mkEnableOption ''
        Whether to enable ProcessIntel services
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
          HTTP address for the ProcessIntel service
        '';
      };

      httpPort = lib.mkOption {
        type = lib.types.int;
        description = ''
          HTTP port for the ProcessIntel service
        '';
      };

      maxUploadSize = lib.mkOption {
        type = lib.types.int;
        default = 200;
        description = ''
          Max Upload size for the ProcessIntel service in GB
        '';
      };

      tmpFileMaxAgeMinutes = lib.mkOption {
        type = lib.types.ints.positive;
        default = 60;
        description = ''
          Maximum age (in minutes) of temporary files.
          Files older than this are automatically removed.
        '';
      };

    };
  };

  config = lib.mkIf cfg.enable {

    systemd.tmpfiles.rules = [
      "d /tmp/${serviceName} 0700 ${user} ${config.services.nginx.group} -"
    ];

    systemd.services.${serviceName} = {
      description = "ProcessIntel service";
      before = [ "nginx.service" ];
      wantedBy = [ "multi-user.target" ];

      path = [ package ];

      environment = {
        PROCESSINTEL_DOCS_DIR = "${package}/docs";

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
        processintel
      '';

      serviceConfig = {
        Group = config.services.nginx.group;
        User = user;

        CacheDirectory = [
          serviceName
          "fontconfig"
        ];
        RuntimeDirectory = serviceName;
        RuntimeDirectoryMode = 750;

        WorkingDirectory = runtimePath;
      };
    };

    systemd.services.processintel-tmp-cleanup = {
      description = "Cleanup tmp files for ProcessIntel service";

      serviceConfig = {
        Type = "oneshot";
        User = user;
        Group = config.services.nginx.group;

        ExecStart = ''
          ${pkgs.findutils}/bin/find /tmp/processintel \
            -type f \
            -mmin +${toString cfg.tmpFileMaxAgeMinutes} \
            -delete
        '';
      };
    };

    systemd.timers.processintel-tmp-cleanup = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = "hourly";
        Persistent = true;
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
      description = "ProcessIntel backend service user";
      group = "nogroup";
      isSystemUser = true;
    };
  };
}
