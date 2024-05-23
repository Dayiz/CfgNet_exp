import os
import sys
import time
import logging
import json
from typing import List
import click

from cfgnet.network.nodes import ArtifactNode
from cfgnet.utility import logger
from cfgnet.network.network import Network
from cfgnet.network.network_configuration import NetworkConfiguration
from cfgnet.launcher_configuration import LauncherConfiguration
from cfgnet.analyze.analyzer import Analyzer
from cfgnet.linker.linker_manager import LinkerManager
from cfgnet.plugins.plugin_manager import PluginManager
from cfgnet.errors.error_detector import ErrorDetector
from cfgnet.constraints.constraint_manager import ConstraintManager


add_project_root_argument = click.argument(
    "project_root", type=click.Path(exists=True)
)

add_enable_linker_option = click.option(
    "--enable-linker",
    type=click.Choice(LinkerManager.get_linker_names()),
    multiple=True,
    default=LinkerManager.get_linker_names,
    help="Specify a linker to be enabled.  If this is not specified, all "
    "available linkers except those explicitly disabled will be used.  "
    "To enable multiple linkers, pass the option for each of them, i.e.  "
    "`--enable-linker foo --enable-linker bar`.",
)
add_disable_linker_option = click.option(
    "--disable-linker",
    type=click.Choice(LinkerManager.get_linker_names()),
    multiple=True,
    default=[],
    help="Specify a linker to be disabled."
    "To enable multiple linkers, pass the option for each of them, i.e.  "
    "`--disable-linker foo --disable-linker bar`.",
)


@click.group()
@click.option(
    "-v", "--verbose", help="Log everything to console.", is_flag=True
)
def main(verbose: bool):
    LauncherConfiguration.verbose = verbose
    logger.configure_console_logger(verbose=verbose)


@main.command()
@click.option("-b", "--enable-static-blacklist", is_flag=True)
@click.option("-i", "--enable-internal-links", is_flag=True)
@click.option("-c", "--enable-all-conflicts", is_flag=True)
@click.option("-f", "--config-files", multiple=True)
@add_project_root_argument
@add_enable_linker_option
@add_disable_linker_option
def init(
    enable_static_blacklist: bool,
    enable_internal_links: bool,
    enable_all_conflicts: bool,
    project_root: str,
    enable_linker: List[str],
    disable_linker: List[str],
    config_files: List,
):
    """Initialize configuration network."""
    project_name = os.path.basename(project_root)
    logging.info("Initialize configuration network for %s.", project_name)

    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(project_root),
        config_files=list(config_files),
        enable_static_blacklist=enable_static_blacklist,
        enable_internal_links=enable_internal_links,
        enabled_linkers=list(set(enable_linker) - set(disable_linker)),
        enable_all_conflicts=enable_all_conflicts,
    )
    LinkerManager.set_enabled_linkers(network_configuration.enabled_linkers)
    logger.configure_repo_logger(network_configuration.logfile_path())

    start = time.time()
    network = Network.init_network(network_configuration)

    network.save()

    completion_time = round((time.time() - start), 2)

    logging.info("Done in [%s s]", str(completion_time))

@main.command()
@add_project_root_argument
def validate(project_root: str):
    """Validate a reference network against a new network."""
    project_name = os.path.basename(project_root)
    logging.info("Validate configuration network for %s.", project_name)

    start = time.time()

    ref_network = Network.load_network(project_root=project_root)
    logger.configure_repo_logger(ref_network.cfg.logfile_path())

    # TODO Network should configure LinkerManager with list of enabled linkers

    conflicts, new_network = ref_network.validate()
    constraint_difference = new_network.option_constraints.difference(ref_network.option_constraints)
    new_network.conflicts = conflicts
    new_network.save()

    if (len(conflicts) + len(constraint_difference))== 0:
        logging.info("No conflicts detected.")
        return

    detected_conflicts = sum((conflict.count() for conflict in conflicts))

    logging.error(
        "Detected %s configuration conflicts", str(detected_conflicts)
    )

    completion_time = round((time.time() - start), 2)

    logging.info("Done in [%s s]", completion_time)

    print()
    for conflict in conflicts:
        print(conflict)

    sys.exit(1)
      
@main.command()
@add_project_root_argument
def checkconstraints(project_root: str):
    """Validating constraints of a network."""
    project_name = os.path.basename(project_root)
    logging.info("Validate constraints configuration network for %s.", project_name)

    start = time.time()

    network = Network.load_network(project_root=project_root)
    logger.configure_repo_logger(network.cfg.logfile_path())

    cm = ConstraintManager()
    node_list = network.get_nodes(ArtifactNode)
    found_violations = []
    for node in node_list:
        result = cm.check_constraints(node)
        if result != None:
            found_violations += result
    network.constraint_violations = found_violations
    network.save()
    if len(found_violations) > 0:
        print()
        print(f"Found Constraint Violations: {len(found_violations)}")
        for violation in found_violations:
            print("===========================================")
            print(violation)

    completion_time = round((time.time() - start), 2)
    logging.info("Done in [%s s]", completion_time)
    sys.exit(1)

@main.command
@add_project_root_argument
def correctconstraints(project_root: str):
    start = time.time()
    network = Network.load_network(project_root=project_root)
    for counter in range(len(network.constraint_violations)):
        obj = network.constraint_violations[counter]
        var = input(f"Please input new Value for {obj.option.display_option_id} in Artifact {obj.artifact.rel_file_path} (expected {obj.option.config_type}-type): ")
        if var == None:
            continue
        network.constraint_violations[counter].old_value = var
    
    errors = ErrorDetector.get_errors_from_conflicts(network.constraint_violations)
    if not errors:
        logging.info("No errors to correct exist.")
        return
    error_count = len(errors)
    corrected_errors = 0
    plugins = PluginManager.get_plugins()
    unresolved_erros = []
    for err in errors:
        if err.wrong_value != None and err.correct_value != None and err.correct_value != "":
            plugin = PluginManager.get_responsible_plugin(plugins, err.file_path)
            if plugin:
                try:
                    plugin.correct_error(err)
                    corrected_errors += 1
                    #ref_network.discard_conflict(error)
                except UnicodeDecodeError as error:
                    unresolved_erros.append(err)
                    logging.warning(
                        "%s: %s (%s) (no correct_error method?)",
                        plugin.__class__.__name__,
                        error.reason
                        )
    logging.info(
            "Corrected %s configuration errors", str(corrected_errors)
        )
    if (error_count - corrected_errors) != 0:
        logging.info(
            "%s configuration errors remain unresolved", str(error_count - corrected_errors)
            )
    completion_time = round((time.time() - start), 2)
    logging.info("Done in [%s s]", completion_time)
    sys.exit(1)
    
@main.command()
@add_project_root_argument
def validateconstraints(project_root: str):
    project_name = os.path.basename(project_root)
    logging.info("Validate configuration network for %s.", project_name)

    start = time.time()
    cm = ConstraintManager()
    ref_network = Network.load_network(project_root=project_root)
    logger.configure_repo_logger(ref_network.cfg.logfile_path())
    new_network = Network.init_network(ref_network.cfg)
    detected_conflicts = ref_network.option_constraints.difference(new_network.option_constraints)
    new_network.constraint_conflicts = cm.convert_templates_to_conflicts(ref_network.option_constraints, new_network.option_constraints)
    new_network.save()

    logging.info(
        f"Detected {len(detected_conflicts)} configuration conflicts"
    )
    print()
    for det in new_network.constraint_conflicts:
        print(det)
    completion_time = round((time.time() - start), 2)

    logging.info("Done in [%s s]", completion_time)

    sys.exit(1)


@main.command()
@click.option("-r", "--replace-old-values", is_flag=True)
@add_project_root_argument
def solve(
    replace_old_values: bool,
    project_root: str    
    ):
    """Try to correct found conflicts"""
    project_name = os.path.basename(project_root)
    logging.info("Validate configuration network for %s.", project_name)

    start = time.time()

    ref_network = Network.load_network(project_root=project_root)
    logger.configure_repo_logger(ref_network.cfg.logfile_path())
    cm = ConstraintManager()
    # 1) Correct Dependency Errors
    # 2) Correct Constraint Errors
    conflicts = ref_network.conflicts.union(ref_network.constraint_conflicts)  
    errors = ErrorDetector.get_errors_from_conflicts(conflicts, replace_old_values)
    if not errors:
        logging.info("No errors detected.")
        return
    else:
        detected_errors = len(errors)
        logging.info(
            "Detected %s configuration errors", str(detected_errors)
        )
    
    plugins = PluginManager.get_plugins()
    unresolved_erros = []
    for err in errors:
        plugin = PluginManager.get_responsible_plugin(plugins, err.file_path)
        if plugin:
            try:
                plugin.correct_error(err)
            except UnicodeDecodeError as error:
                unresolved_erros.append(err)
                logging.warning(
                    "%s: %s (%s) (no correct_error method?)",
                    plugin.__class__.__name__,
                    error.reason
                    )
                
    
    #TODO Check which conflicts have been resolved, update conflicts for network
        
    solved_network = Network.init_network(ref_network.cfg)
    solved_network.conflicts = ref_network.conflicts
    solved_network.save()

    completion_time = round((time.time() - start), 2)
    if len(unresolved_erros) != 0:
        logging.info("Unresolved Errors: %s", str(len(unresolved_erros)))
        for ue in unresolved_erros:
            logging.info(ue.conflict_id)
    logging.info("Done in [%s s]", completion_time)

    sys.exit(1)


@main.command()
@click.option("-b", "--enable-static-blacklist", is_flag=True)
@click.option("-i", "--enable-internal-links", is_flag=True)
@click.option("-c", "--enable-all-conflicts", is_flag=True)
@click.option("-f", "--config-files", multiple=True)
@add_project_root_argument
@add_enable_linker_option
@add_disable_linker_option
def analyze(
    enable_static_blacklist: bool,
    enable_internal_links: bool,
    enable_all_conflicts: bool,
    project_root: str,
    enable_linker: List[str],
    disable_linker: List[str],
    config_files: List,
):
    """Run self-evaluating analysis of commit history."""
    project_name = os.path.basename(project_root)

    logging.info("Analyzing commit history for %s.", project_name)

    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(project_root),
        config_files=list(config_files),
        enable_static_blacklist=enable_static_blacklist,
        enable_internal_links=enable_internal_links,
        enabled_linkers=list(set(enable_linker) - set(disable_linker)),
        enable_all_conflicts=enable_all_conflicts,
    )
    LinkerManager.set_enabled_linkers(network_configuration.enabled_linkers)
    logger.configure_repo_logger(network_configuration.logfile_path())

    enabled_linkers = set(enable_linker) - set(disable_linker)
    LinkerManager.set_enabled_linkers(enabled_linkers)

    start = time.time()

    analyzer = Analyzer(cfg=network_configuration)

    analyzer.analyze_commit_history()

    completion_time = round((time.time() - start), 2)

    logging.info(
        "Analysis of %s done in [%s s].", project_name, completion_time
    )


@main.command()
@click.option("-o", "--output", required=True)  # TODO type
@click.option("-f", "--format", "export_format", required=True)  # TODO type
@click.option("-u", "--include-unlinked", is_flag=True)  # TODO type
@click.option("-v", "--visualize-dot", is_flag=True)  # TODO type
@add_project_root_argument
def export(
    output: str,
    export_format: str,
    include_unlinked: bool,
    visualize_dot: bool,
    project_root: str,
):
    """Export a configuration network."""
    LauncherConfiguration.export_output = output
    LauncherConfiguration.export_format = export_format
    LauncherConfiguration.export_include_unlinked = include_unlinked
    LauncherConfiguration.export_visualize_dot = visualize_dot

    network = Network.load_network(project_root)
    logger.configure_repo_logger(network.cfg.logfile_path())

    if LauncherConfiguration.export_visualize_dot:
        logging.info("Visualize the configuration network.")

        network.visualize(
            name=LauncherConfiguration.export_output,
            export_format=LauncherConfiguration.export_format,
            include_unlinked=LauncherConfiguration.export_include_unlinked,
        )
        return

    logging.info("Export the configuration network.")

    network.export(
        name=LauncherConfiguration.export_output,
        export_format=LauncherConfiguration.export_format,
        include_unlinked=LauncherConfiguration.export_include_unlinked,
    )


@main.command()
@click.option("-f", "--config-files", multiple=True)
@click.option("-o", "--output", required=True)
@add_project_root_argument
def extract(
    project_root: str,
    config_files: List,
    output: str,
):
    """Extract key-value pairs."""
    project_name = os.path.basename(project_root)
    logging.info("Extract key-value pairs for %s.", project_name)

    network_configuration = NetworkConfiguration(
        project_root_abs=os.path.abspath(project_root),
        config_files=list(config_files),
        enable_static_blacklist=False,
        enable_internal_links=False,
        enable_all_conflicts=False,
    )

    start = time.time()

    network = Network.init_network(network_configuration)

    key_value_pairs = network.get_pairs()

    output_path = os.path.join(
        output, network_configuration.project_name() + "_options.json"
    )

    logging.info("Store key-value pairs in %s.", output_path)

    with open(output_path, "w", encoding="utf-8") as dest:
        json.dump(key_value_pairs, dest, sort_keys=True, indent=4)

    completion_time = round((time.time() - start), 2)

    logging.info("Done in [%s s]", str(completion_time))


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
