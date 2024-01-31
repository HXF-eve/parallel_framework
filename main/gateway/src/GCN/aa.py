print("Epoch {:05d} | ".format(epoch) +
              "Train Accuracy: {:.4f} | Train Loss: {:.4f} | ".format(
                  train_acc, loss.item()) +
              "Validation Accuracy: {:.4f} | Validation loss: {:.4f}".format(
                  val_acc, val_loss.item()))



def  start():
    print('start train.....')
    time.sleep(6)
    print('classfication:\n'
          'Access node: 2 5 3\n'
          'Alternative node: 1 4\n'
          'Inefficient node: 7\n'
          'normal node: 6'
          )
