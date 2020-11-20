from waflib import Utils
from waflib.extras.test_base import summary
from waflib.extras.symwaf2ic import get_toplevel_path


def depends(dep):
    pass


def options(opt):
    opt.load("shelltest")


def configure(cfg):
    cfg.load("shelltest")


def build(bld):
    bld.install_files("${PREFIX}/bin",
                      bld.path.ant_glob("src/shell/**/*"),
                      chmod=Utils.O755,
                      name="tools-slurm_shellscripts")

    bld(name="tools-slurm_shellscripts_tests",
        tests=bld.path.ant_glob("tests/shell/**/*"),
        features="use shelltest",
        use="tools-slurm_shellscripts",
        test_environ=dict(WAF_TOPLEVEL=get_toplevel_path()))

    bld.add_post_fun(summary)
