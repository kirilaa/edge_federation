import altair as alt
import json
import time
import pandas as pd
import sys
import os


results_path= "../../results/"
file_type = ".html"

def plot_data(data):
    data_values = data.values()
    data_values = list(data_values)
    data_values = data_values[2:]
    
    data_keys = data.keys()
    data_keys = list(data_keys)
    data_keys = data_keys[2:]

    plot_data = pd.DataFrame({'time':data_values, 'phases':data_keys})

    plot = alt.Chart(plot_data).mark_bar().encode( x= 'time', y= alt.Y('phases',sort='x'), color='phases')

    return plot

def reduce_data(data):
    data = list(data)
    data = data[2:]
    return data

def reverse_data(data):
    data_reversed = [None]*len(data)
    for i,e, in reversed(list(enumerate(data))):
        if i>0:
            data_reversed[i] = data[i]-data[i-1]
        else:
            data_reversed[i]=data[i]
    return data_reversed


def combine_plots(consumer_data, provider_data):
    consumer_values = reduce_data(consumer_data.values())
    provider_values = reduce_data(provider_data.values())
    provider_keys = reduce_data(provider_data.keys())
    consumer_keys = reduce_data(consumer_data.keys())
    
    consumer_values = reverse_data(consumer_values)
    provider_values = reverse_data(provider_values)

    consumer_label = ['consumer']*len(consumer_keys)
    provider_label = ['provider']*len(provider_keys)

    c_plot_data = pd.DataFrame({'time':consumer_values, 'phases':consumer_keys, 'domain':consumer_label})
    p_plot_data = pd.DataFrame({'time':provider_values, 'phases':provider_keys, 'domain':provider_label})

    # c_plot = alt.Chart(c_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color='phases')
    # p_plot = alt.Chart(p_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color='phases')
    c_plot = alt.Chart(c_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color=alt.Color('phases', legend= None))
    p_plot = alt.Chart(p_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color=alt.Color('phases', legend= None))
    
    # c_plot = alt.Chart(c_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color=alt.Color('phases', legend= alt.Legend(orient="bottom")))
    # p_plot = alt.Chart(p_plot_data).mark_bar().encode( x= 'time', y= alt.Y('domain', sort='x'), color=alt.Color('phases', legend= alt.Legend(orient="bottom")))
    
    plot = c_plot + p_plot

    return plot




if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('[Usage] {} result_consumer result_provider'.format(
            sys.argv[0]))
        exit(0)
    else:
        with open(results_path+sys.argv[1]+".json") as consumer_file:
            consumer_data = json.load(consumer_file)

        with open(results_path+sys.argv[2]+".json") as provider_file:
            provider_data = json.load(provider_file)

    plot_consumer = plot_data(consumer_data)
    plot_provider = plot_data(provider_data)

    cobined_plot = combine_plots(consumer_data, provider_data)
    combined_file_string = sys.argv[1].split('_')[0] + "_combined"
    plot_consumer.save(results_path+sys.argv[1]+file_type, scale_factor=2.0)
    plot_provider.save(results_path+sys.argv[2]+file_type, scale_factor=2.0)
    cobined_plot.save(results_path+combined_file_string+file_type, scale_factor=2.0)