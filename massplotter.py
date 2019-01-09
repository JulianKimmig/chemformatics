import matplotlib.pyplot as plt

def mass_plot(x,y,labels=None,norm=False,title=None):
    for i in range(len(y)):
  
            plt.plot(x[:len(y[i])],y[i]/((y[i].max() if y[i].max() !=0 else 1) if norm else 1),label=( str(labels[i]) if labels is not None else None))
    if labels is not None:
        plt.legend()
    if title is not None:
        plt.title(str(title))
     
    plt.show()  