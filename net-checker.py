import click
import json
import os
import matplotlib.pyplot as plt
import numpy as np

COLORS = [
    "red",
    "green",
    "blue",
    "cyan",
    "magenta",
    "black",
    "gray",
    "purple",
    "orange",
    "brown",
    "pink",
    "violet",
    "gold",
    "silver",
    "teal",
    "indigo",
    "lime",
    "maroon",
    "navy",
    "olive",
]


def load_json_files(folder):
    """Load JSON files from a single directory, categorizing by protocol."""
    scenario_data = {}

    # Get list of files in the folder
    files = {
        f.replace(".json", ""): f for f in os.listdir(folder) if f.endswith(".json")
    }

    for scenario, filename in files.items():
        with open(os.path.join(folder, filename), "r") as f:
            json_data = json.load(f)["end"]
            if scenario.lower().startswith("tcp"):
                sent_bps = json_data.get("sum_sent", {}).get("bits_per_second", 0)
                recv_bps = json_data.get("sum_received", {}).get("bits_per_second", 0)
                scenario_data[scenario] = {
                    "protocol": "tcp",
                    "sent_bps": sent_bps,
                    "recv_bps": recv_bps,
                }
            elif scenario.lower().startswith("udp"):
                udp_bps = json_data.get("sum", {}).get("bits_per_second", 0)
                lost_percent = json_data.get("sum", {}).get("lost_percent", 0)
                scenario_data[scenario] = {
                    "protocol": "udp",
                    "bps": udp_bps,
                    "lost_percent": lost_percent,
                }

    return scenario_data


def collect_scenario_data(net_data, source, target, scenarios):
    """Collect data from multiple folders, returning a dictionary with folder names as keys."""
    folder_data = {}
    folders = []
    for scenario in scenarios:
        folder = os.path.join(net_data, scenario, source, "iperf", target)
        # Load data from each folder
        folder_name = os.path.basename(folder)
        scenario_data = load_json_files(folder)
        folder_data[scenario] = scenario_data

    return folder_data


def plot_tcp_diagram(
    folder_data, output_file="tcp_scenario_comparison.svg", format="svg"
):
    """Generate a bar diagram for TCP sent bits per second across folders."""
    # Collect TCP scenarios
    tcp_scenarios = sorted(
        set(
            s
            for folder in folder_data.values()
            for s in folder
            if folder.get(s, {}).get("protocol") == "tcp"
        )
    )

    if not tcp_scenarios:
        print("No TCP scenarios to plot.")
        return

    # Get folder names from folder_data
    folders = sorted(folder_data.keys())
    num_folders = len(folders)
    x = np.arange(len(tcp_scenarios))
    width = 0.8 / num_folders  # Adjust width for one bar per folder, matching UDP

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, folder_name in enumerate(folders):
        sent_bps = [
            folder_data.get(folder_name, {}).get(s, {"sent_bps": 0})["sent_bps"]
            / 1_000_000_000
            for s in tcp_scenarios
        ]

        # Plot sent bars, positioned similarly to UDP
        offset = (i - num_folders / 2 + 0.5) * width
        ax.bar(
            x + offset,
            sent_bps,
            width,
            label=f"{folder_name}: Sent (Gbps)",
            color=COLORS[i],
        )

    ax.set_xlabel("Scenarios")
    ax.set_ylabel("Throughput (Gbps)")
    ax.set_title("TCP Sent Throughput Comparison Across Scenarios")
    ax.set_xticks(x)
    ax.set_xticklabels(tcp_scenarios, rotation=45, ha="right")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0)

    plt.tight_layout()
    plt.savefig(output_file, format=format, bbox_inches="tight")
    plt.close()
    print(f"TCP bar diagram saved as '{output_file}'")


def plot_udp_diagram(
    folder_data, output_file="udp_scenario_comparison.svg", format="svg"
):
    """Generate a bar diagram for UDP bits per second with vertically printed lost packet percentages."""
    # Collect UDP scenarios
    udp_scenarios = sorted(
        set(
            s
            for folder in folder_data.values()
            for s in folder
            if folder.get(s, {}).get("protocol") == "udp"
        )
    )

    if not udp_scenarios:
        print("No UDP scenarios to plot.")
        return

    # Get folder names from folder_data
    folders = sorted(folder_data.keys())
    num_folders = len(folders)
    x = np.arange(len(udp_scenarios))

    width = 0.8 / num_folders  # Adjust width based on number of folders

    fig, ax = plt.subplots(figsize=(20, 6))

    for i, folder_name in enumerate(folders):
        bps = [
            folder_data.get(folder_name, {}).get(s, {"bps": 0})["bps"] / 1_000_000_000
            for s in udp_scenarios
        ]
        lost_percent = [
            folder_data.get(folder_name, {}).get(s, {"lost_percent": 0})["lost_percent"]
            for s in udp_scenarios
        ]

        # Plot bars with clear folder name in legend
        bars = ax.bar(
            x + (i - num_folders / 2 + 0.5) * width,
            bps,
            width,
            label=f"{folder_name}: Throughput (Gbps)",
            color=COLORS[i],
        )

        # Add lost packet percentage as vertically printed text above each bar
        for j, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height,
                f"{lost_percent[j]:.2f}%",
                ha="center",
                va="bottom",
                fontsize=10,
                rotation=90,
            )

    ax.set_xlabel("Scenarios")
    ax.set_ylabel("Throughput (Gbps)")
    ax.set_ylim(0)  # Set y-axis to start at 0
    ax.set_title("UDP Throughput Comparison Across Scenarios")
    ax.set_xticks(x)
    ax.set_xticklabels(udp_scenarios, rotation=45, ha="right")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0)

    plt.tight_layout()
    plt.savefig(output_file, format=format, bbox_inches="tight")
    plt.close()
    print(f"UDP bar diagram saved as '{output_file}'")


def main(format="svg"):
    # Specify the directories containing JSON files
    net_data = "./net_checker_reports"
    out_dir = "./"

    # Create list of source, target scenarios
    targets = {}
    scenario_folders = [
        x for x in os.listdir(net_data) if os.path.isdir(os.path.join(net_data, x))
    ]
    for scenario in scenario_folders:
        for source_host in os.listdir(os.path.join(net_data, scenario)):
            target_hosts = os.path.join(net_data, scenario, source_host, "iperf")
            for target_host in os.listdir(target_hosts):
                targets.setdefault((source_host, target_host), [])
                targets[(source_host, target_host)].append(scenario)

    # Create uniq report per source + target with all scenarios
    for source_target, scenarios in targets.items():
        source = source_target[0]
        target = source_target[1]

        folder_data = collect_scenario_data(net_data, source, target, scenarios)
        out_file = f"{source}_{target}.{format}"

        # Check if there are any scenarios to plot
        if not any(folder_data.values()):
            print("No scenarios found to plot.")
            return

        # Generate TCP bar diagram if TCP scenarios exist
        if any(
            s
            for folder in folder_data.values()
            for s in folder
            if folder[s].get("protocol") == "tcp"
        ):
            plot_tcp_diagram(
                folder_data, os.path.join(out_dir, f"tcp_{out_file}"), format
            )

        # Generate UDP bar diagram if UDP scenarios exist
        if any(
            s
            for folder in folder_data.values()
            for s in folder
            if folder[s].get("protocol") == "udp"
        ):
            plot_udp_diagram(
                folder_data, os.path.join(out_dir, f"udp_{out_file}"), format
            )


@click.group()
def cli():
    """A simple CLI tool using Click"""
    pass


@cli.command()
@click.option("--format", default="svg", help="Output format")
def report(format):
    main(format=format)


if __name__ == "__main__":
    cli()
