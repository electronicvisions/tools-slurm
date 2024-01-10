from os.path import join
from waflib import Utils
from waflib.extras.test_base import summary
from waflib.extras.symwaf2ic import get_toplevel_path


def depends(dep):
    dep('code-format')


def options(opt):
    opt.load("shelltest")
    opt.load('pytest')
    opt.load('pylint')
    opt.load('pycodestyle')


def configure(cfg):
    cfg.load("shelltest")
    cfg.load('python')
    cfg.load('pytest')
    cfg.load('pylint')
    cfg.load('pycodestyle')


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

    bld(name='tools-slurm_pythonscripts',
        features='use py pylint pycodestyle',
        source=bld.path.ant_glob('src/py/**/*.py'),
        relative_trick=True,
        install_from='src/py',
        install_path='${PREFIX}/bin',
        chmod=Utils.O755,
        pylint_config=join(get_toplevel_path(), "code-format", "pylintrc"),
        pycodestyle_config=join(get_toplevel_path(), "code-format", "pycodestyle"),
        )

    bld(name="tools-slurm_pythonscripts_tests",
        tests=bld.path.ant_glob("tests/py/**/*.py"),
        features='use pytest pylint pycodestyle',
        use="tools-slurm_pythonscripts",
        pylint_config=join(get_toplevel_path(), "code-format", "pylintrc"),
        pycodestyle_config=join(get_toplevel_path(), "code-format", "pycodestyle"),
        )

    bld.add_post_fun(summary)
