import pandas as pd
import matplotlib.pyplot as plt
import mpld3

def finish_plot(plot_title, save_fig="off"):
        plt.xlabel("Time (elapsed seconds)")
        plt.legend(markerscale=3)
        plt.grid(True, alpha=0.5)
        plt.title(plot_title) # + "\n" + run)
        if save_fig == "png":
            plt.savefig("Figure_{}.png".format(plt.gcf().number))
        elif save_fig == "html":
            mpld3.save_html(plt.gcf(), "Figure_{}.html".format(plt.gcf().number))

df_all_obj = pd.read_csv("core_validation/environment_roadway_objects.csv")

plt.rcParams['scatter.marker'] = '.'
plt.rcParams['figure.figsize'] = [8, 6]
plt.rcParams['lines.markersize'] = 3

df_all_obj['elapsed_time'] = (df_all_obj['rosbagTimestamp'] - min(df_all_obj['rosbagTimestamp']))/1000000000.0
grouped = df_all_obj.groupby('elapsed_time').count()

plt.figure(1)
plt.scatter(grouped.index, grouped.object_id, label="message")
plt.ylabel("Number of objects")
finish_plot("Objects detected on roadway per message") #, "png")

unique_ids = df_all_obj.object_id.drop_duplicates().astype(int).astype(str).to_list()
plt.figure(2, figsize=(8,12)) # may want to adjust across runs
plt.scatter(df_all_obj.elapsed_time, df_all_obj.object_id.astype(int).astype(str), label="message")
plt.yticks(unique_ids, fontsize=6)
plt.ylabel("Object ID")
finish_plot("Object presence over time") #, "png")

plt.show()