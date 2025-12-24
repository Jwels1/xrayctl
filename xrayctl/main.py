import sys

from xrayctl.xrayparser import build_parser
from xrayctl.config import load_settings
from xrayctl.output import print_out
from xrayctl.api.client import XrayClient
from xrayctl.errors import XrayHTTPError
from xrayctl.workflows import system as system_wf
from xrayctl.workflows import config as config_wf
from xrayctl.workflows import ignore_rules as ignore_wf



def _require(value: str | None, name: str) -> str:
    if not value:
        raise ValueError(f"Missing required setting: {name} (provide flag, env, or config)")
    return value


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    settings = load_settings(
        url=args.url,
        token=args.token,
        project=args.project,
        timeout=args.timeout,
        fmt=args.format,
        config_path=args.config,
    )

    try:
        if args.command == "hello":
            print("xrayctl is wired up ✅")
            return
        
        h = getattr(args, "handler", None)

        if h == "config_init":
            out = config_wf.init_config(args.config)
            print_out(out, fmt=settings.fmt)
            return

        if h == "config_view":
            out = config_wf.view_effective(args)
            print_out(out, fmt=settings.fmt)
            return

        if h == "config_set":
            out = config_wf.set_value(args.config, args.key, args.value)
            print_out(out, fmt=settings.fmt)
            return

        if h == "config_save":
            out = config_wf.save_from_flags(args)
            print_out(out, fmt=settings.fmt)
            return

        url = _require(settings.url, "url")
        token = _require(settings.token, "token")

        client = XrayClient(
            base_url=url,
            token=token,
            timeout=settings.timeout,
            project=settings.project,
        )

        if getattr(args, "handler", None) == "ignore_rules_create":
            out = ignore_wf.create(
                client,
                note=args.note,
                watches=args.watch,
                cves=args.cve,
                vulns=args.vuln,
                licenses=args.license,
                expires_at=args.expires_at,
                dry_run = args.dry_run
            )
            print_out(out, fmt=settings.fmt)
            return
        
        if getattr(args, "handler", None) == "ignore_rules_list":
            out = ignore_wf.list_rules(
                client,
                watch=args.watch,
                policy=args.policy,
                vulnerability=args.vulnerability,
                cve=args.cve,
                license_name=args.license,
                component_name=args.component_name,
                component_version=args.component_version,
                page=args.page,
                rows=args.rows,
                order_by=args.order_by,
                direction=args.direction,
                expires_before=args.expires_before,
                expires_after=args.expires_after,
                fetch_all=args.all,
            )
            print_out(out, fmt=settings.fmt)
            return

        if getattr(args, "handler", None) == "ignore_rules_get":
            out = ignore_wf.get_rule(client, args.id)
            print_out(out, fmt=settings.fmt)
            return


        if getattr(args, "handler", None) == "ping":
            out = system_wf.ping(client)
            print_out(out, fmt=settings.fmt)
            return

        raise ValueError(f"Unknown handler: {getattr(args, 'handler', None)}")

    except XrayHTTPError as e:
        print_out(
            {"ok": False, "error": str(e), "status_code": e.status_code, "details": e.details},
            fmt=settings.fmt,
        )
        sys.exit(2)

    except Exception as e:
        print_out({"ok": False, "error": str(e)}, fmt=settings.fmt)
        sys.exit(1)
